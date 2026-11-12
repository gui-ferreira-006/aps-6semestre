"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)

Motor Biométrico Facial — As 5 Fases do Processamento Digital de Imagens
==============================================================================

Este módulo implementa, de forma explícita e didática, o pipeline clássico
de Processamento Digital de Imagens exigido pelo edital da APS, aplicado ao
reconhecimento facial do operador diante do terminal do cofre:

    ┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
    │  FASE 1      │──▶│  FASE 2          │──▶│  FASE 3      │
    │  Aquisição   │   │  Pré-processam.  │   │  Segmentação │
    │ (Base64→BGR) │   │ (resize, CLAHE,  │   │ (HOG → ROI)  │
    └──────────────┘   │  BGR→RGB)        │   └──────┬───────┘
                       └──────────────────┘          │
    ┌──────────────────────┐   ┌─────────────────────▼──────┐
    │  FASE 5              │◀──│  FASE 4                    │
    │  Classificação       │   │  Extração de Características│
    │ (Distância Euclid.)  │   │ (ResNet-34 dlib → 128D)    │
    └──────────────────────┘   └────────────────────────────┘

Princípios de projeto:
  * 100% DESACOPLADO DE BANCO DE DADOS: opera apenas sobre strings Base64 e
    vetores numéricos em memória. A camada de persistência (SQLAlchemy /
    MySQL) apenas armazenará/fornecerá o vetor de 128 floats.
  * Exceções de domínio específicas, que carregam o código de erro e o
    status HTTP sugerido (400 = falha de captura/entrada; 401 = falha de
    reconhecimento; 503 = motor indisponível), mantendo a camada web fina.
  * Tipagem estrita (typing / numpy.typing) e compatibilidade com Pyright e
    Pyrefly, inclusive em máquinas onde o ``face_recognition`` (dlib) NÃO
    está instalado — ele é carregado sob demanda (lazy loading).

Uso típico:
    >>> from biometria import cadastrar_biometria, autenticar_biometria
    >>> vetor = cadastrar_biometria(foto_base64)          # Fases 1 → 4
    >>> resultado = autenticar_biometria(frame_b64, vetor) # Fases 1 → 5
    >>> resultado.reconhecido, resultado.distancia_euclidiana
"""

from __future__ import annotations

import base64
import binascii
import importlib
import json
import logging
import math
import os
import re
import time
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Dict,
    Final,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import cv2
import numpy as np
from numpy.typing import NDArray

# Logger dedicado ao motor biométrico (telemetria das fases e da decisão).
logger = logging.getLogger("faca.biometria")


# =============================================================================
# 0. CONSTANTES, TIPOS E PARÂMETROS CONFIGURÁVEIS
# =============================================================================

#: Dimensionalidade do descritor facial gerado pela ResNet-34 do dlib.
DIMENSAO_VETOR: Final[int] = 128

#: Variável de ambiente que parametriza o limiar de decisão (threshold).
VARIAVEL_TOLERANCIA: Final[str] = "FACE_RECOGNITION_TOLERANCE"

#: Tolerância padrão. O default da biblioteca é 0.60; adotamos 0.50 (mais
#: rigoroso) por se tratar de um cofre de segurança máxima: reduz a Taxa de
#: Falsa Aceitação (FAR) ao custo de um leve aumento da Falsa Rejeição (FRR).
TOLERANCIA_PADRAO: Final[float] = 0.50

#: Maior lado (em pixels) permitido após o pré-processamento. Webcams Full HD
#: (1920x1080) são reduzidas para 800x450, o que mantém a face do operador
#: (tipicamente > 150 px) muito acima do mínimo exigido pelo detector HOG
#: (~80 px, ou ~40 px com upsample=1), preservando os landmarks faciais.
DIMENSAO_MAXIMA_PADRAO_PX: Final[int] = 800

#: Menor lado aceito para a imagem adquirida (abaixo disso não há face útil).
DIMENSAO_MINIMA_PX: Final[int] = 64

#: Teto de caracteres da string Base64 (~10 MB ≈ 7,5 MB binários). Protege o
#: servidor contra payloads abusivos (negação de serviço por memória).
TAMANHO_MAXIMO_BASE64: Final[int] = 10 * 1024 * 1024

#: Modelo do detector facial: "hog" (CPU, rápido) ou "cnn" (GPU/lento).
MODELO_DETECCAO_PADRAO: Final[str] = "hog"

#: Quantas vezes a imagem é ampliada internamente pelo detector (ajuda a
#: encontrar rostos pequenos — como transeuntes ao fundo, o que reforça a
#: regra de "apenas um operador por vez").
UPSAMPLE_PADRAO: Final[int] = 1

#: Limiares (canal L do espaço CIELAB, escala 0–255) que disparam a
#: normalização de iluminação na Fase 2. Imagens bem expostas não são
#: alteradas, preservando a fidelidade do descritor.
LIMIAR_LUMINANCIA_MEDIA: Final[float] = 70.0
LIMIAR_CONTRASTE_DESVIO: Final[float] = 25.0

#: Parâmetros do CLAHE (Contrast Limited Adaptive Histogram Equalization).
CLAHE_CLIP_LIMIT: Final[float] = 2.0
CLAHE_GRADE: Final[Tuple[int, int]] = (8, 8)

# ── Aliases de tipo (legibilidade e tipagem estrita) ──
ImagemBGR = NDArray[np.uint8]
"""Matriz H×W×3 (uint8) no padrão nativo do OpenCV: Azul, Verde, Vermelho."""

ImagemRGB = NDArray[np.uint8]
"""Matriz H×W×3 (uint8) no padrão exigido pelo dlib: Vermelho, Verde, Azul."""

TuplaCaixa = Tuple[int, int, int, int]
"""Caixa delimitadora no padrão do face_recognition: (top, right, bottom, left)."""

VetorBiometrico = List[float]
"""Descritor facial de 128 floats, serializável em JSON."""

VetorEntrada = Union[Sequence[float], NDArray[np.floating[Any]]]
"""Qualquer vetor numérico aceito na entrada (lista Python ou array NumPy)."""

ModeloDeteccao = Literal["hog", "cnn"]

K = TypeVar("K", bound=Hashable)


# =============================================================================
# 1. EXCEÇÕES CUSTOMIZADAS DO DOMÍNIO BIOMÉTRICO
# =============================================================================
# Hierarquia:
#
#   BiometriaError (500)
#    ├── ErroCapturaBiometricaError (400)  → problema na ENTRADA / captura
#    │    ├── ImagemBase64InvalidaError        INVALID_IMAGE
#    │    ├── NenhumRostoDetectadoError        NO_FACE_DETECTED
#    │    ├── MultiplosRostosDetectadosError   MULTIPLE_FACES_DETECTED
#    │    ├── VetorBiometricoInvalidoError     INVALID_FACE_VECTOR
#    │    └── ExtracaoCaracteristicasError     FEATURE_EXTRACTION_FAILED
#    ├── FalhaReconhecimentoError (401)    → captura OK, mas identidade NEGADA
#    │    └── RostoNaoReconhecidoError         FACE_NOT_RECOGNIZED
#    ├── FalhaInternaBiometriaError (500)      BIOMETRIC_PROCESSING_ERROR
#    └── MotorBiometricoIndisponivelError (503) BIOMETRIC_ENGINE_UNAVAILABLE
#
# Cada exceção carrega `codigo` (legível por máquina, usado pelo Frontend),
# `status_http` (sugestão para a camada FastAPI), `mensagem` humanizada e
# `detalhes` opcionais — exatamente a estrutura do envelope de erro do API.md.
# =============================================================================

class BiometriaError(Exception):
    """Exceção-base de todo o domínio biométrico do F.A.C.A."""

    codigo: ClassVar[str] = "BIOMETRIC_ERROR"
    status_http: ClassVar[int] = 500
    mensagem_padrao: ClassVar[str] = "Falha no processamento biométrico."

    def __init__(
        self,
        mensagem: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.mensagem: str = mensagem or self.mensagem_padrao
        self.detalhes: Optional[Dict[str, Any]] = detalhes
        super().__init__(self.mensagem)

    def para_dict(self) -> Dict[str, Any]:
        """Serializa no formato do objeto ``erro`` do contrato (API.md)."""
        return {
            "codigo": self.codigo,
            "mensagem": self.mensagem,
            "detalhes": self.detalhes,
        }


# ── 1.1 Erros de entrada / captura → HTTP 400 ──

class ErroCapturaBiometricaError(BiometriaError):
    """Família de erros causados pela imagem/vetor enviado (HTTP 400)."""

    codigo: ClassVar[str] = "BIOMETRIC_CAPTURE_ERROR"
    status_http: ClassVar[int] = 400
    mensagem_padrao: ClassVar[str] = "A captura biométrica enviada é inválida."


class ImagemBase64InvalidaError(ErroCapturaBiometricaError):
    """String Base64 vazia, malformada ou que não decodifica em JPEG/PNG."""

    codigo: ClassVar[str] = "INVALID_IMAGE"
    mensagem_padrao: ClassVar[str] = (
        "A imagem enviada é inválida, corrompida ou está vazia. "
        "Envie uma captura JPEG ou PNG codificada em Base64."
    )


class NenhumRostoDetectadoError(ErroCapturaBiometricaError):
    """A Fase 3 (segmentação) não encontrou nenhuma face no quadro."""

    codigo: ClassVar[str] = "NO_FACE_DETECTED"
    mensagem_padrao: ClassVar[str] = (
        "Nenhum rosto foi detectado na imagem. Centralize seu rosto no "
        "enquadramento e certifique-se de estar em um ambiente iluminado."
    )

    def __init__(
        self,
        mensagem: Optional[str] = None,
        detalhes: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensagem, detalhes or {"rostos_encontrados": 0})


class MultiplosRostosDetectadosError(ErroCapturaBiometricaError):
    """
    Regra de segurança do cofre: apenas UM operador por vez diante do
    terminal. Mais de uma face no quadro bloqueia preventivamente o acesso
    (mitiga "carona" / tailgating e coação).
    """

    codigo: ClassVar[str] = "MULTIPLE_FACES_DETECTED"

    def __init__(self, quantidade: int, mensagem: Optional[str] = None) -> None:
        self.quantidade: int = quantidade
        super().__init__(
            mensagem
            or (
                f"Múltiplos rostos detectados ({quantidade}). Por motivos de "
                "segurança, apenas uma pessoa deve estar visível para a "
                "autenticação."
            ),
            {"rostos_encontrados": quantidade},
        )


class VetorBiometricoInvalidoError(ErroCapturaBiometricaError):
    """Vetor de referência/capturado sem 128 dimensões ou com NaN/Inf."""

    codigo: ClassVar[str] = "INVALID_FACE_VECTOR"
    mensagem_padrao: ClassVar[str] = (
        f"O vetor biométrico deve conter exatamente {DIMENSAO_VETOR} valores "
        "numéricos finitos."
    )


class ExtracaoCaracteristicasError(ErroCapturaBiometricaError):
    """A rede neural não conseguiu gerar o descritor para a face segmentada."""

    codigo: ClassVar[str] = "FEATURE_EXTRACTION_FAILED"
    mensagem_padrao: ClassVar[str] = (
        "Não foi possível extrair as características faciais. Tente uma "
        "nova captura com o rosto frontal e bem iluminado."
    )


# ── 1.2 Falhas de reconhecimento → HTTP 401 ──

class FalhaReconhecimentoError(BiometriaError):
    """Família de falhas em que a captura é válida mas a identidade não."""

    codigo: ClassVar[str] = "BIOMETRIC_RECOGNITION_FAILED"
    status_http: ClassVar[int] = 401
    mensagem_padrao: ClassVar[str] = "Falha no reconhecimento biométrico."


class RostoNaoReconhecidoError(FalhaReconhecimentoError):
    """A distância euclidiana excedeu a tolerância (impostor ou baixa qualidade)."""

    codigo: ClassVar[str] = "FACE_NOT_RECOGNIZED"
    mensagem_padrao: ClassVar[str] = (
        "Acesso Negado: a biometria facial não corresponde ao usuário informado."
    )

    def __init__(
        self,
        resultado: Optional[ResultadoComparacao] = None,
        mensagem: Optional[str] = None,
    ) -> None:
        self.resultado: Optional[ResultadoComparacao] = resultado
        super().__init__(mensagem, resultado.para_dict() if resultado else None)


# ── 1.3 Falhas de infraestrutura → HTTP 500 / 503 ──

class FalhaInternaBiometriaError(BiometriaError):
    """Erro inesperado nos bindings C++ do dlib / OpenCV."""

    codigo: ClassVar[str] = "BIOMETRIC_PROCESSING_ERROR"
    status_http: ClassVar[int] = 500
    mensagem_padrao: ClassVar[str] = (
        "Erro interno no processamento da imagem biométrica."
    )


class MotorBiometricoIndisponivelError(BiometriaError):
    """A biblioteca face_recognition/dlib não está instalada neste ambiente."""

    codigo: ClassVar[str] = "BIOMETRIC_ENGINE_UNAVAILABLE"
    status_http: ClassVar[int] = 503
    mensagem_padrao: ClassVar[str] = (
        "Motor biométrico indisponível: a biblioteca 'face_recognition' (dlib) "
        "não está instalada neste ambiente. Execute o backend via Docker."
    )


# =============================================================================
# 2. ESTRUTURAS DE DADOS DE RESULTADO (imutáveis)
# =============================================================================

@dataclass(frozen=True)
class CaixaDelimitadora:
    """
    Região de Interesse (ROI) da face, no padrão do face_recognition:
    ``top`` (y inicial), ``right`` (x final), ``bottom`` (y final),
    ``left`` (x inicial) — coordenadas em pixels.
    """

    top: int
    right: int
    bottom: int
    left: int

    @property
    def largura(self) -> int:
        return self.right - self.left

    @property
    def altura(self) -> int:
        return self.bottom - self.top

    def como_tupla(self) -> TuplaCaixa:
        """Formato exigido pelo argumento ``known_face_locations`` do dlib."""
        return (self.top, self.right, self.bottom, self.left)

    def reescalar(self, fator: float, largura_max: int, altura_max: int) -> CaixaDelimitadora:
        """
        Converte a caixa das coordenadas da imagem REDUZIDA (Fase 2) para as
        coordenadas da imagem ORIGINAL, dividindo pelo fator de escala e
        limitando (clamp) aos limites da matriz original.
        """
        if fator <= 0 or math.isclose(fator, 1.0):
            return self

        def _ajustar(valor: int, limite: int) -> int:
            return int(min(max(round(valor / fator), 0), limite))

        return CaixaDelimitadora(
            top=_ajustar(self.top, altura_max),
            right=_ajustar(self.right, largura_max),
            bottom=_ajustar(self.bottom, altura_max),
            left=_ajustar(self.left, largura_max),
        )

    def para_dict(self) -> Dict[str, int]:
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
        }


@dataclass(frozen=True, eq=False)
class ImagemPreProcessada:
    """Saída da Fase 2: matriz RGB contígua + metadados do pré-processamento."""

    rgb: ImagemRGB
    fator_escala: float
    dimensoes_originais: Tuple[int, int]    # (largura, altura)
    dimensoes_processadas: Tuple[int, int]  # (largura, altura)
    iluminacao_normalizada: bool


@dataclass(frozen=True)
class ResultadoExtracao:
    """Saída consolidada das Fases 1 → 4 (usada no cadastro e na telemetria)."""

    vetor: VetorBiometrico
    caixa_processada: CaixaDelimitadora
    caixa_original: CaixaDelimitadora
    dimensoes_originais: Tuple[int, int]
    dimensoes_processadas: Tuple[int, int]
    fator_escala: float
    iluminacao_normalizada: bool
    tempos_ms: Dict[str, float]

    @property
    def tempo_total_ms(self) -> float:
        return round(sum(self.tempos_ms.values()), 2)


@dataclass(frozen=True)
class ResultadoComparacao:
    """Saída da Fase 5 (verificação 1:1)."""

    reconhecido: bool
    distancia_euclidiana: float
    tolerancia: float
    confianca_percentual: float

    def para_dict(self) -> Dict[str, Any]:
        return {
            "reconhecido": self.reconhecido,
            "distancia_euclidiana": self.distancia_euclidiana,
            "tolerancia": self.tolerancia,
            "confianca_percentual": self.confianca_percentual,
        }


@dataclass(frozen=True)
class ResultadoIdentificacao(Generic[K]):
    """Saída da identificação 1:N (busca do candidato mais próximo)."""

    reconhecido: bool
    identificador: Optional[K]
    melhor_comparacao: Optional[ResultadoComparacao]
    total_candidatos: int


# =============================================================================
# 3. CONFIGURAÇÃO VIA VARIÁVEIS DE AMBIENTE
# =============================================================================

def _ler_float_env(nome: str, padrao: float, minimo: float, maximo: float) -> float:
    """Lê um float do ambiente (aceita vírgula decimal) com validação de faixa."""
    bruto = os.getenv(nome)
    if bruto is None or not bruto.strip():
        return padrao
    try:
        valor = float(bruto.strip().replace(",", "."))
    except ValueError:
        logger.warning("%s=%r inválido; usando padrão %.2f.", nome, bruto, padrao)
        return padrao
    if not (minimo < valor <= maximo) or not math.isfinite(valor):
        logger.warning(
            "%s=%s fora da faixa (%s, %s]; usando padrão %.2f.",
            nome, valor, minimo, maximo, padrao,
        )
        return padrao
    return valor


def _ler_int_env(nome: str, padrao: int, minimo: int, maximo: int) -> int:
    """Lê um inteiro do ambiente com validação de faixa [minimo, maximo]."""
    bruto = os.getenv(nome)
    if bruto is None or not bruto.strip():
        return padrao
    try:
        valor = int(bruto.strip())
    except ValueError:
        logger.warning("%s=%r inválido; usando padrão %d.", nome, bruto, padrao)
        return padrao
    return valor if minimo <= valor <= maximo else padrao


def obter_tolerancia() -> float:
    """
    Limiar de decisão da Fase 5, lido de ``FACE_RECOGNITION_TOLERANCE``.
    Faixa aceita: (0, 1]. Fallback: 0.50. Lido a cada chamada para permitir
    ajuste em tempo de execução/testes sem reiniciar o processo.
    """
    return _ler_float_env(VARIAVEL_TOLERANCIA, TOLERANCIA_PADRAO, 0.0, 1.0)


def obter_dimensao_maxima() -> int:
    """Maior lado após o downscaling da Fase 2 (``FACE_MAX_IMAGE_DIMENSION``)."""
    return _ler_int_env("FACE_MAX_IMAGE_DIMENSION", DIMENSAO_MAXIMA_PADRAO_PX, 160, 4096)


def obter_modelo_deteccao() -> ModeloDeteccao:
    """Detector da Fase 3 (``FACE_DETECTION_MODEL``): 'hog' (padrão) ou 'cnn'."""
    modelo = os.getenv("FACE_DETECTION_MODEL", MODELO_DETECCAO_PADRAO).strip().lower()
    return "cnn" if modelo == "cnn" else "hog"


def obter_upsample() -> int:
    """Nº de ampliações internas do detector (``FACE_DETECTION_UPSAMPLE``)."""
    return _ler_int_env("FACE_DETECTION_UPSAMPLE", UPSAMPLE_PADRAO, 0, 3)


# =============================================================================
# 4. CARREGAMENTO SOB DEMANDA DO face_recognition (dlib)
# =============================================================================
# O face_recognition depende do dlib compilado em C++ (disponível apenas na
# imagem Docker). Importá-lo no topo do módulo quebraria a análise estática e
# a execução de ferramentas no Windows. Por isso:
#   1. Declaramos um Protocol com as assinaturas que realmente usamos
#      (tipagem estrita, mesmo sem stubs da biblioteca);
#   2. Importamos o módulo dinamicamente apenas na primeira utilização.
# =============================================================================

class _MotorFaceRecognition(Protocol):
    """Contrato tipado mínimo da API pública do face_recognition 1.3.x."""

    def face_locations(
        self,
        img: ImagemRGB,
        number_of_times_to_upsample: int = ...,
        model: str = ...,
    ) -> List[TuplaCaixa]: ...

    def face_encodings(
        self,
        face_image: ImagemRGB,
        known_face_locations: Optional[List[TuplaCaixa]] = ...,
        num_jitters: int = ...,
        model: str = ...,
    ) -> List[NDArray[np.float64]]: ...


_motor_cache: Optional[_MotorFaceRecognition] = None


def _carregar_motor() -> _MotorFaceRecognition:
    """Importa (uma única vez) e devolve o módulo face_recognition."""
    global _motor_cache
    if _motor_cache is None:
        try:
            modulo = importlib.import_module("face_recognition")
        except (ImportError, OSError, SystemExit) as exc:
            # SystemExit: o face_recognition chama quit() quando o pacote
            # face_recognition_models não está instalado.
            raise MotorBiometricoIndisponivelError() from exc
        _motor_cache = cast(_MotorFaceRecognition, modulo)
        logger.info("Motor face_recognition (dlib) carregado com sucesso.")
    return _motor_cache


def motor_disponivel() -> bool:
    """Indica se o motor dlib pode ser carregado neste ambiente."""
    try:
        _carregar_motor()
    except MotorBiometricoIndisponivelError:
        return False
    return True


# =============================================================================
# 5. FASE 1 — AQUISIÇÃO DA IMAGEM
# =============================================================================
# Objetivo: transformar a captura da webcam, transportada como texto Base64 no
# JSON, de volta em uma matriz digital de pixels f(x, y) manipulável.
#
#   String Base64 ──b64decode──▶ bytes JPEG/PNG ──np.frombuffer──▶ vetor 1D
#   uint8 ──cv2.imdecode──▶ matriz H×W×3 (BGR, uint8)
#
# O cabeçalho Data URL (``data:image/jpeg;base64,``) gerado por
# ``canvas.toDataURL()`` é removido automaticamente, assim como quebras de
# linha e espaços. Também aceitamos o alfabeto Base64-URL (``-`` e ``_``) e
# corrigimos padding ausente (``=``).
# =============================================================================

_REGEX_DATA_URL: Final[re.Pattern[str]] = re.compile(
    r"^data:[^,;]*(?:;[^,;]+)*;base64,", re.IGNORECASE
)
_REGEX_ESPACOS: Final[re.Pattern[str]] = re.compile(r"\s+")


def sanitizar_base64(imagem_base64: str) -> str:
    """
    Normaliza a string recebida do Frontend para Base64 padrão (RFC 4648):
    remove o prefixo Data URL, espaços/quebras de linha, converte o alfabeto
    URL-safe e restaura o padding. Lança ``ImagemBase64InvalidaError`` se o
    conteúdo resultante for vazio ou exceder o tamanho máximo.
    """
    texto = _REGEX_DATA_URL.sub("", (imagem_base64 or "").strip(), count=1)
    texto = _REGEX_ESPACOS.sub("", texto)

    if not texto:
        raise ImagemBase64InvalidaError("A imagem Base64 enviada está vazia.")
    if len(texto) > TAMANHO_MAXIMO_BASE64:
        raise ImagemBase64InvalidaError(
            "A imagem enviada excede o tamanho máximo permitido (~7,5 MB).",
            {"tamanho_base64": len(texto), "limite": TAMANHO_MAXIMO_BASE64},
        )

    # Alfabeto Base64-URL → Base64 padrão e restauração do padding '='.
    texto = texto.replace("-", "+").replace("_", "/").rstrip("=")
    return texto + "=" * (-len(texto) % 4)


def fase1_aquisicao(imagem_base64: str) -> ImagemBGR:
    """
    FASE 1 — Aquisição: decodifica a string Base64 em uma matriz BGR.

    Returns:
        Matriz NumPy H×W×3 (uint8) no espaço de cores BGR (padrão OpenCV).

    Raises:
        ImagemBase64InvalidaError: Base64 vazio/malformado, bytes que não
            formam uma imagem JPEG/PNG válida ou dimensões insuficientes.
    """
    texto = sanitizar_base64(imagem_base64)

    # 1.a) Texto Base64 → bytes brutos do arquivo de imagem (JPEG/PNG).
    #      validate=True rejeita caracteres fora do alfabeto Base64.
    try:
        dados = base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImagemBase64InvalidaError(
            "A string enviada não é um Base64 válido."
        ) from exc
    if not dados:
        raise ImagemBase64InvalidaError("A imagem decodificada está vazia.")

    # 1.b) Bytes → vetor unidimensional uint8 (sem cópia de memória).
    buffer: NDArray[np.uint8] = np.frombuffer(dados, dtype=np.uint8)

    # 1.c) Decodificação do formato comprimido (JPEG/PNG) para a matriz de
    #      pixels. IMREAD_COLOR garante 3 canais BGR mesmo para imagens em
    #      tons de cinza ou com canal alfa (PNG RGBA).
    try:
        matriz = cast(Optional[NDArray[Any]], cv2.imdecode(buffer, cv2.IMREAD_COLOR))
    except cv2.error as exc:
        raise ImagemBase64InvalidaError(
            "Os dados enviados não correspondem a uma imagem JPEG/PNG válida."
        ) from exc
    if matriz is None or matriz.size == 0:
        raise ImagemBase64InvalidaError(
            "Os dados enviados não correspondem a uma imagem JPEG/PNG válida "
            "ou o arquivo está corrompido."
        )

    imagem: ImagemBGR = np.asarray(matriz, dtype=np.uint8)

    # 1.d) Validação estrutural da matriz adquirida.
    if imagem.ndim != 3 or imagem.shape[2] != 3:
        raise ImagemBase64InvalidaError(
            "A imagem decodificada não possui 3 canais de cor.",
            {"shape": list(imagem.shape)},
        )
    altura, largura = int(imagem.shape[0]), int(imagem.shape[1])
    if min(altura, largura) < DIMENSAO_MINIMA_PX:
        raise ImagemBase64InvalidaError(
            f"Resolução insuficiente ({largura}x{altura}). O menor lado deve "
            f"ter pelo menos {DIMENSAO_MINIMA_PX} pixels.",
            {"largura": largura, "altura": altura},
        )

    return imagem


# =============================================================================
# 6. FASE 2 — PRÉ-PROCESSAMENTO
# =============================================================================
# Objetivo: condicionar a matriz para as próximas fases, maximizando a
# acurácia e minimizando a latência:
#
#   2.a) Redimensionamento proporcional (downscaling) com interpolação
#        INTER_AREA — reamostragem por área de pixel, que atua como filtro
#        passa-baixa e evita aliasing/moiré. O custo do detector HOG é
#        proporcional ao nº de pixels: 1920x1080 → 800x450 é ~5,8× mais rápido.
#   2.b) Normalização CONDICIONAL de iluminação via CLAHE aplicada SOMENTE
#        ao canal de luminância L* (CIELAB), preservando a crominância. Só é
#        acionada em quadros escuros ou de baixo contraste, para não alterar
#        capturas já adequadas.
#   2.c) Conversão do espaço de cores BGR (OpenCV) → RGB (dlib).
#   2.d) Garantia de layout C-contíguo em memória (np.ascontiguousarray),
#        requisito dos bindings pybind11/C++ do dlib — fatias e conversões
#        podem gerar "views" com strides não contíguos.
# =============================================================================

def _normalizar_iluminacao(imagem_bgr: ImagemBGR) -> Tuple[ImagemBGR, bool]:
    """Aplica CLAHE no canal L* se a imagem estiver escura ou sem contraste."""
    lab = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2LAB)
    canal_l, canal_a, canal_b = cv2.split(lab)

    luminancia_media = float(np.mean(canal_l))
    contraste_desvio = float(np.std(canal_l))
    if (
        luminancia_media >= LIMIAR_LUMINANCIA_MEDIA
        and contraste_desvio >= LIMIAR_CONTRASTE_DESVIO
    ):
        return imagem_bgr, False

    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_GRADE)
    canal_l_equalizado = clahe.apply(canal_l)
    lab_equalizado = cv2.merge((canal_l_equalizado, canal_a, canal_b))
    resultado = np.asarray(cv2.cvtColor(lab_equalizado, cv2.COLOR_LAB2BGR), dtype=np.uint8)

    logger.debug(
        "Fase 2: CLAHE aplicado (L* médio=%.1f, desvio=%.1f).",
        luminancia_media, contraste_desvio,
    )
    return resultado, True


def fase2_preprocessamento(
    imagem_bgr: ImagemBGR,
    dimensao_maxima: Optional[int] = None,
) -> ImagemPreProcessada:
    """
    FASE 2 — Pré-processamento: downscaling, normalização de iluminação,
    conversão BGR→RGB e contiguidade de memória.

    Args:
        imagem_bgr: Matriz produzida pela Fase 1.
        dimensao_maxima: Maior lado permitido (padrão: ``obter_dimensao_maxima()``).

    Returns:
        ``ImagemPreProcessada`` com a matriz RGB e o fator de escala aplicado
        (necessário para remapear a caixa delimitadora à imagem original).
    """
    limite = dimensao_maxima if dimensao_maxima and dimensao_maxima > 0 else obter_dimensao_maxima()
    altura, largura = int(imagem_bgr.shape[0]), int(imagem_bgr.shape[1])

    # 2.a) Redimensionamento proporcional (mantém a razão de aspecto).
    fator_escala = 1.0
    trabalho: ImagemBGR = imagem_bgr
    maior_lado = max(altura, largura)
    if maior_lado > limite:
        fator_escala = limite / float(maior_lado)
        nova_largura = max(1, int(round(largura * fator_escala)))
        nova_altura = max(1, int(round(altura * fator_escala)))
        trabalho = np.asarray(
            cv2.resize(imagem_bgr, (nova_largura, nova_altura), interpolation=cv2.INTER_AREA),
            dtype=np.uint8,
        )

    # 2.b) Normalização condicional de iluminação/contraste (CLAHE em L*).
    trabalho, iluminacao_normalizada = _normalizar_iluminacao(trabalho)

    # 2.c) BGR → RGB: o OpenCV armazena os canais na ordem Azul-Verde-Vermelho;
    #      o dlib/face_recognition espera Vermelho-Verde-Azul.
    rgb = cv2.cvtColor(trabalho, cv2.COLOR_BGR2RGB)

    # 2.d) Matriz C-contígua e uint8 para os bindings C++ do dlib.
    rgb_contigua: ImagemRGB = np.ascontiguousarray(rgb, dtype=np.uint8)

    return ImagemPreProcessada(
        rgb=rgb_contigua,
        fator_escala=round(fator_escala, 6),
        dimensoes_originais=(largura, altura),
        dimensoes_processadas=(int(rgb_contigua.shape[1]), int(rgb_contigua.shape[0])),
        iluminacao_normalizada=iluminacao_normalizada,
    )


# =============================================================================
# 7. FASE 3 — SEGMENTAÇÃO (DETECÇÃO FACIAL)
# =============================================================================
# Objetivo: isolar a Região de Interesse (ROI) que contém a face humana,
# separando-a do fundo da cena.
#
# Detector padrão: HOG (Histogram of Oriented Gradients) + SVM linear com
# janela deslizante em pirâmide de imagens (dlib). O HOG descreve a forma
# local pela distribuição das orientações de gradiente, sendo robusto a
# pequenas variações de iluminação e rápido em CPU. Alternativa: "cnn"
# (MMOD), mais precisa em ângulos difíceis, porém muito mais lenta sem GPU.
#
# Regra de negócio do cofre (estrita):
#   0 faces  → NenhumRostoDetectadoError       (HTTP 400)
#   >1 faces → MultiplosRostosDetectadosError  (HTTP 400)
#   1 face   → retorna (top, right, bottom, left)
# =============================================================================

def fase3_segmentacao(
    imagem_rgb: ImagemRGB,
    modelo: Optional[ModeloDeteccao] = None,
    upsample: Optional[int] = None,
) -> CaixaDelimitadora:
    """
    FASE 3 — Segmentação: localiza exatamente UMA face na imagem RGB.

    Raises:
        NenhumRostoDetectadoError: nenhuma face encontrada.
        MultiplosRostosDetectadosError: mais de uma face encontrada.
        FalhaInternaBiometriaError: erro nos bindings do dlib.
    """
    motor = _carregar_motor()
    modelo_efetivo: ModeloDeteccao = modelo or obter_modelo_deteccao()
    upsample_efetivo = obter_upsample() if upsample is None else upsample

    try:
        localizacoes = motor.face_locations(
            imagem_rgb,
            number_of_times_to_upsample=upsample_efetivo,
            model=modelo_efetivo,
        )
    except RuntimeError as exc:  # ex.: "Unsupported image type"
        raise FalhaInternaBiometriaError(
            f"Falha no detector facial ({modelo_efetivo}): {exc}"
        ) from exc

    quantidade = len(localizacoes)
    if quantidade == 0:
        raise NenhumRostoDetectadoError()
    if quantidade > 1:
        raise MultiplosRostosDetectadosError(quantidade)

    top, right, bottom, left = localizacoes[0]
    return CaixaDelimitadora(top=int(top), right=int(right), bottom=int(bottom), left=int(left))


# =============================================================================
# 8. FASE 4 — EXTRAÇÃO DE CARACTERÍSTICAS (FEATURE EXTRACTION — 128D)
# =============================================================================
# Objetivo: reduzir a ROI (milhares de pixels) a um descritor numérico
# compacto e discriminativo — um ponto em R^128.
#
#   4.a) Alinhamento: o dlib estima 5 landmarks (cantos dos olhos e base do
#        nariz) e normaliza a face (rotação/escala) para um "chip" 150×150.
#   4.b) Embedding: a rede ResNet-34 (29 camadas convolucionais), treinada
#        com *metric learning* (triplet/pair loss) em ~3 milhões de faces,
#        projeta o chip em um vetor de 128 dimensões no qual faces da MESMA
#        pessoa ficam próximas e de pessoas DIFERENTES ficam distantes
#        (acurácia de 99,38% no benchmark LFW).
#   4.c) Serialização: o vetor NumPy (float64) é convertido para list[float]
#        pura, pronta para JSON (coluna do MySQL) ou comparação imediata.
# =============================================================================

def validar_vetor(vetor: VetorEntrada, nome: str = "vetor") -> NDArray[np.float64]:
    """
    Garante que o vetor possua exatamente 128 valores finitos e o devolve
    como array NumPy float64 1D (formato ideal para a álgebra da Fase 5).
    """
    try:
        array: NDArray[np.float64] = np.asarray(vetor, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise VetorBiometricoInvalidoError(
            f"O {nome} contém valores não numéricos."
        ) from exc

    if array.ndim != 1 or array.shape[0] != DIMENSAO_VETOR:
        raise VetorBiometricoInvalidoError(
            f"O {nome} deve ter {DIMENSAO_VETOR} dimensões "
            f"(recebido: shape {list(array.shape)}).",
            {"dimensoes_recebidas": int(array.size), "dimensoes_esperadas": DIMENSAO_VETOR},
        )
    if not bool(np.all(np.isfinite(array))):
        raise VetorBiometricoInvalidoError(f"O {nome} contém valores NaN ou infinitos.")
    return array


def fase4_extracao_caracteristicas(
    imagem_rgb: ImagemRGB,
    caixa: CaixaDelimitadora,
    num_jitters: int = 1,
) -> VetorBiometrico:
    """
    FASE 4 — Extração do descritor facial de 128 dimensões.

    Args:
        imagem_rgb: Matriz RGB contígua da Fase 2.
        caixa: ROI obtida na Fase 3 (evita uma segunda detecção).
        num_jitters: Nº de reamostragens aleatórias da face cuja média forma
            o descritor (maior = mais estável, porém mais lento).

    Returns:
        Lista Python com 128 floats.
    """
    motor = _carregar_motor()
    try:
        descritores = motor.face_encodings(
            imagem_rgb,
            known_face_locations=[caixa.como_tupla()],
            num_jitters=max(1, num_jitters),
            model="small",  # preditor de 5 landmarks (alinhamento recomendado pelo dlib)
        )
    except RuntimeError as exc:
        raise FalhaInternaBiometriaError(
            f"Falha na rede de extração de características: {exc}"
        ) from exc

    if len(descritores) != 1:
        raise ExtracaoCaracteristicasError(
            detalhes={"descritores_gerados": len(descritores)}
        )

    vetor_np = validar_vetor(descritores[0], "descritor extraído")
    return [float(valor) for valor in vetor_np.tolist()]


# =============================================================================
# 9. FASE 5 — CLASSIFICAÇÃO E INTERPRETAÇÃO (VERIFICAÇÃO 1:1 / IDENTIFICAÇÃO 1:N)
# =============================================================================
# Objetivo: decidir se dois descritores pertencem à mesma pessoa.
#
# Métrica: Distância Euclidiana (norma L2) no espaço de 128 dimensões:
#
#        d(v1, v2) = ‖v1 − v2‖₂ = sqrt( Σᵢ (v1ᵢ − v2ᵢ)² ),  i = 1..128
#
# Regra de decisão (classificador por limiar):
#        d ≤ tolerância  →  MATCH (mesma identidade)    → acesso biométrico OK
#        d > tolerância  →  NO MATCH (impostor)         → acesso negado
#
# Interpretação: a rede foi treinada para que pares genuínos fiquem tipicamente
# abaixo de 0.6. Usamos 0.50 (configurável) para priorizar a segurança.
#
# Confiança percentual (apenas telemetria/log — NÃO participa da decisão):
# mapeamento não linear e monotônico da distância para [0, 100] %, calibrado
# para valer exatamente 50 % no limiar, crescer rapidamente para ~100 % quando
# d → 0 e decrescer linearmente para 0 % quando d → 1.
# =============================================================================

def calcular_distancia_euclidiana(vetor_a: VetorEntrada, vetor_b: VetorEntrada) -> float:
    """Calcula ‖a − b‖₂ entre dois descritores de 128 dimensões."""
    a = validar_vetor(vetor_a, "vetor capturado")
    b = validar_vetor(vetor_b, "vetor de referência")
    return float(np.linalg.norm(a - b))


def distancia_para_confianca(distancia: float, tolerancia: float) -> float:
    """
    Converte a distância euclidiana em similaridade percentual [0, 100].

    * Acima do limiar: queda linear de 50 % (d = tol) até 0 % (d = 1).
    * Abaixo do limiar: base linear de 50 % a 100 % acrescida de uma curva
      de potência (expoente 0,2) que "achata" o topo, refletindo que
      distâncias bem abaixo do limiar são praticamente certeza de match.
    """
    tol = min(max(tolerancia, 1e-6), 1.0 - 1e-6)
    if distancia > tol:
        linear = (1.0 - distancia) / ((1.0 - tol) * 2.0)
        confianca = linear
    else:
        linear = 1.0 - (distancia / (tol * 2.0))
        confianca = linear + (1.0 - linear) * math.pow((linear - 0.5) * 2.0, 0.2)
    return round(min(max(confianca, 0.0), 1.0) * 100.0, 2)


def fase5_classificacao(
    vetor_capturado: VetorEntrada,
    vetor_referencia: VetorEntrada,
    tolerancia: Optional[float] = None,
) -> ResultadoComparacao:
    """
    FASE 5 — Verificação 1:1 entre o descritor da webcam e o de referência.

    Args:
        vetor_capturado: Descritor 128D recém-extraído (Fase 4).
        vetor_referencia: Descritor 128D armazenado no cadastro do usuário.
        tolerancia: Limiar de decisão (padrão: ``FACE_RECOGNITION_TOLERANCE``
            ou 0.50).

    Returns:
        ``ResultadoComparacao`` com match, distância (4 casas) e confiança %.
    """
    limiar = tolerancia if tolerancia is not None and 0.0 < tolerancia <= 1.0 else obter_tolerancia()
    distancia = calcular_distancia_euclidiana(vetor_capturado, vetor_referencia)
    resultado = ResultadoComparacao(
        reconhecido=distancia <= limiar,
        distancia_euclidiana=round(distancia, 4),
        tolerancia=round(limiar, 4),
        confianca_percentual=distancia_para_confianca(distancia, limiar),
    )
    logger.info(
        "Fase 5: d=%.4f | tolerância=%.2f | confiança=%.2f%% | match=%s",
        resultado.distancia_euclidiana, resultado.tolerancia,
        resultado.confianca_percentual, resultado.reconhecido,
    )
    return resultado


def identificar_1_n(
    vetor_capturado: VetorEntrada,
    candidatos: Mapping[K, VetorEntrada],
    tolerancia: Optional[float] = None,
) -> ResultadoIdentificacao[K]:
    """
    Identificação 1:N — compara o descritor capturado com N referências
    (ex.: ``{id_usuario: vetor}``) e devolve o candidato de MENOR distância.
    Só há reconhecimento se essa menor distância estiver dentro do limiar.

    Implementação vetorizada: empilha os N vetores em uma matriz N×128 e
    calcula todas as normas L2 de uma vez (np.linalg.norm com axis=1).
    """
    if not candidatos:
        return ResultadoIdentificacao(False, None, None, 0)

    limiar = tolerancia if tolerancia is not None and 0.0 < tolerancia <= 1.0 else obter_tolerancia()
    alvo = validar_vetor(vetor_capturado, "vetor capturado")
    chaves: List[K] = list(candidatos.keys())
    matriz = np.vstack([validar_vetor(candidatos[c], f"vetor do candidato {c!r}") for c in chaves])

    distancias: NDArray[np.float64] = np.linalg.norm(matriz - alvo, axis=1)
    indice = int(np.argmin(distancias))
    menor = float(distancias[indice])
    comparacao = ResultadoComparacao(
        reconhecido=menor <= limiar,
        distancia_euclidiana=round(menor, 4),
        tolerancia=round(limiar, 4),
        confianca_percentual=distancia_para_confianca(menor, limiar),
    )
    return ResultadoIdentificacao(
        reconhecido=comparacao.reconhecido,
        identificador=chaves[indice] if comparacao.reconhecido else None,
        melhor_comparacao=comparacao,
        total_candidatos=len(chaves),
    )


# =============================================================================
# 10. API DE ALTO NÍVEL (ORQUESTRAÇÃO DAS FASES)
# =============================================================================

def extrair_caracteristicas(imagem_base64: str, num_jitters: int = 1) -> ResultadoExtracao:
    """
    Executa as Fases 1 → 4 sobre uma imagem Base64 e devolve o descritor
    128D acompanhado de metadados (ROI, dimensões, escala, tempos por fase).
    """
    tempos: Dict[str, float] = {}

    inicio = time.perf_counter()
    imagem_bgr = fase1_aquisicao(imagem_base64)
    tempos["fase1_aquisicao"] = (time.perf_counter() - inicio) * 1000.0

    inicio = time.perf_counter()
    pre = fase2_preprocessamento(imagem_bgr)
    tempos["fase2_preprocessamento"] = (time.perf_counter() - inicio) * 1000.0

    inicio = time.perf_counter()
    caixa = fase3_segmentacao(pre.rgb)
    tempos["fase3_segmentacao"] = (time.perf_counter() - inicio) * 1000.0

    inicio = time.perf_counter()
    vetor = fase4_extracao_caracteristicas(pre.rgb, caixa, num_jitters=num_jitters)
    tempos["fase4_extracao"] = (time.perf_counter() - inicio) * 1000.0

    largura_orig, altura_orig = pre.dimensoes_originais
    return ResultadoExtracao(
        vetor=vetor,
        caixa_processada=caixa,
        caixa_original=caixa.reescalar(pre.fator_escala, largura_orig, altura_orig),
        dimensoes_originais=pre.dimensoes_originais,
        dimensoes_processadas=pre.dimensoes_processadas,
        fator_escala=pre.fator_escala,
        iluminacao_normalizada=pre.iluminacao_normalizada,
        tempos_ms={fase: round(ms, 2) for fase, ms in tempos.items()},
    )


def cadastrar_biometria(imagem_base64: str, num_jitters: int = 1) -> VetorBiometrico:
    """
    Fluxo de CADASTRO (Fases 1 → 4): devolve o vetor de 128 floats validado,
    pronto para ser persistido (ver ``serializar_vetor``) no MySQL.
    """
    return extrair_caracteristicas(imagem_base64, num_jitters=num_jitters).vetor


def autenticar_biometria(
    imagem_base64: str,
    vetor_referencia: VetorEntrada,
    tolerancia: Optional[float] = None,
    lancar_se_negado: bool = False,
) -> ResultadoComparacao:
    """
    Fluxo de AUTENTICAÇÃO 1:1 (Fases 1 → 5): compara a captura da webcam com
    o vetor de referência do usuário identificado por CPF + senha.

    Args:
        imagem_base64: Frame da webcam (Base64, com ou sem Data URL).
        vetor_referencia: Descritor 128D armazenado no cadastro.
        tolerancia: Limiar opcional (padrão: variável de ambiente / 0.50).
        lancar_se_negado: Se True, lança ``RostoNaoReconhecidoError`` (401)
            quando não houver match, em vez de retornar o resultado.
    """
    # O vetor de referência é validado ANTES do custoso pipeline de imagem.
    referencia = validar_vetor(vetor_referencia, "vetor de referência")
    extracao = extrair_caracteristicas(imagem_base64)
    resultado = fase5_classificacao(extracao.vetor, referencia, tolerancia)
    if lancar_se_negado and not resultado.reconhecido:
        raise RostoNaoReconhecidoError(resultado)
    return resultado


# =============================================================================
# 11. UTILITÁRIOS DE SERIALIZAÇÃO (ponte para a futura camada SQLAlchemy)
# =============================================================================

def serializar_vetor(vetor: VetorEntrada) -> str:
    """Converte o descritor 128D em texto JSON compacto (coluna JSON/TEXT)."""
    return json.dumps([float(v) for v in validar_vetor(vetor).tolist()], separators=(",", ":"))


def desserializar_vetor(dado: Union[str, bytes, Sequence[float]]) -> VetorBiometrico:
    """Reconstrói o descritor 128D a partir do valor lido do banco."""
    bruto: Any = json.loads(dado) if isinstance(dado, (str, bytes)) else dado
    return [float(v) for v in validar_vetor(bruto, "vetor armazenado").tolist()]


__all__ = [
    # Constantes
    "DIMENSAO_VETOR", "TOLERANCIA_PADRAO", "VARIAVEL_TOLERANCIA",
    # Exceções
    "BiometriaError", "ErroCapturaBiometricaError", "ImagemBase64InvalidaError",
    "NenhumRostoDetectadoError", "MultiplosRostosDetectadosError",
    "VetorBiometricoInvalidoError", "ExtracaoCaracteristicasError",
    "FalhaReconhecimentoError", "RostoNaoReconhecidoError",
    "FalhaInternaBiometriaError", "MotorBiometricoIndisponivelError",
    # Estruturas
    "CaixaDelimitadora", "ImagemPreProcessada", "ResultadoExtracao",
    "ResultadoComparacao", "ResultadoIdentificacao",
    # Fases
    "fase1_aquisicao", "fase2_preprocessamento", "fase3_segmentacao",
    "fase4_extracao_caracteristicas", "fase5_classificacao", "identificar_1_n",
    # Alto nível e utilitários
    "extrair_caracteristicas", "cadastrar_biometria", "autenticar_biometria",
    "obter_tolerancia", "motor_disponivel", "sanitizar_base64", "validar_vetor",
    "calcular_distancia_euclidiana", "distancia_para_confianca",
    "serializar_vetor", "desserializar_vetor",
]
