# 🛡️ F.A.C.A. — Contrato de Integração da API (Backend & Frontend)

> **Documento:** Especificação Técnica de Endpoints e Contrato de Dados  
> **Projeto:** F.A.C.A. (Frente de Autenticação e Controle de Acesso) — APS 6º Semestre (UNIP 2026/2)  
> **Stack Backend:** Python 3.11+ / FastAPI / OpenCV / Uvicorn  
> **Destinatária Principal:** Júlia Fernandes (Desenvolvimento Frontend)  
> **Autor / Responsável Backend:** Guilherme (Backend & Visão Computacional)  
> **Versão da API:** `v1.0.0`

---

## 1. Informações Gerais e Diretrizes de Integração

### 1.1. Base URL e Documentação Interativa
* **Ambiente de Desenvolvimento Local:** `http://localhost:8000`
* **Swagger UI (OpenAPI interativo):** `http://localhost:8000/docs`
* **Redoc:** `http://localhost:8000/redoc`

> 💡 **Dica para o Frontend:** Durante os testes, você pode acessar `http://localhost:8000/docs` no navegador para disparar requisições manualmente e visualizar os schemas do Pydantic em tempo real.

### 1.2. Padrão de Comunicação
* **Protocolo:** HTTP/1.1
* **Formato de Dados:** `JSON` (`Content-Type: application/json; charset=utf-8`) em todas as rotas que enviam e recebem payload.
* **Codificação:** UTF-8.

### 1.3. Política de CORS (Cross-Origin Resource Sharing)
O FastAPI está pré-configurado com `CORSMiddleware` liberando origens locais de desenvolvimento, permitindo que o frontend faça chamadas assíncronas sem bloqueios de segurança do navegador.

* **Origens liberadas:** `http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:5500` (Live Server do VS Code) e `http://localhost:8080`.
* **Métodos liberados:** `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.
* **Cabeçalhos permitidos:** `Content-Type`, `Authorization`, `Accept`, `X-Requested-With`.
* **Credenciais:** `allow_credentials=True`.

---

## 2. Padrão de Envio de Imagens Biométricas (Atenção Especial ⚠️)

O motor de Visão Computacional (OpenCV/NumPy) processa buffers binários puros de imagem. Para evitar overhead de conversão desnecessário no servidor:

### ⚠️ Regra do Base64 e Tolerância de Integração:
O campo `imagem_base64` idealmente deve conter a string Base64 pura. No entanto, para evitar quebras de integração caso o Frontend envie o cabeçalho gerado por `canvas.toDataURL()`, o backend **sanitiza e remove automaticamente** qualquer prefixo `data:image/...;base64,`, além de quebras de linha e espaços.

* 💡 **Recomendado (Base64 puro):**
  ```text
  /9j/4AAQSkZJRgABAQEASABIAAD...
  ```
* 🛡️ **Tolerado (com cabeçalho Data URL — sanitizado automaticamente pelo backend):**
  ```text
  data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD...
  ```

### ✂️ Snippet Utilitário para o Frontend (JavaScript):
Ao capturar o frame do `<video>` via `<canvas>`, utilize a seguinte função sanitizadora antes de anexar a imagem ao JSON:

```javascript
/**
 * Captura o frame de um elemento <video> desenhado em um <canvas>
 * e retorna a string Base64 limpa, sem o cabeçalho data:image/...
 * 
 * @param {HTMLCanvasElement} canvasElement 
 * @returns {string} Base64 puro da imagem JPEG
 */
function capturarBase64Puro(canvasElement) {
    const dataUrl = canvasElement.toDataURL('image/jpeg', 0.9); // 90% de qualidade
    return dataUrl.replace(/^data:image\/[a-z]+;base64,/, '');
}
```

---

## 3. Matriz de Níveis de Acesso (Controle de Privilégios)

O sistema do Ministério do Meio Ambiente opera com controle de acesso baseado em papéis (RBAC) com **3 níveis de segurança estritos**:

| Nível | Descrição do Acesso | Perfil de Usuário Típico | Visibilidade no Cofre de Toxinas |
|:---:|---|---|---|
| **1** | **Acesso Geral / Operacional** | Pesquisadores, técnicos de laboratório | Toxinas de baixo risco biológico (grau educacional / amostras controladas comuns). |
| **2** | **Acesso Intermediário** | Diretores de divisões específicas | Toxinas de classe moderada e alta (agentes biológicos industriais e táticos controlados). |
| **3** | **Acesso Máximo / Irrestrito** | Ministro do Meio Ambiente e Gabinete Crítico | Acesso total irrestrito (incluindo armas químicas/biológicas letais e Quimeras Nível 4). |

---

## 4. Especificação dos Endpoints

---

### 4.1. Health Check (Teste de Conectividade)

Utilizado pelo Frontend ao carregar a aplicação para validar se o servidor FastAPI está operacional antes de abrir a câmera ou exibir o formulário.

* **Método:** `GET`
* **Rota:** `/ping`
* **Autenticação:** Não necessária (Pública)

#### Requisição
```http
GET /ping HTTP/1.1
Host: localhost:8000
Accept: application/json
```

#### Resposta de Sucesso (`200 OK`)
```json
{
  "status": "ok",
  "mensagem": "Servidor F.A.C.A. operacional",
  "versao": "1.0.0",
  "timestamp": "2026-09-06T20:50:00Z"
}
```

---

### 4.2. Autenticação Multifator (MFA 1:1) — CPF + Senha + Biometria Facial

Implementa o fluxo de autenticação multifator exigido pelo Roteiro Oficial v2 do Ministério do Meio Ambiente, combinando três fatores de autenticação:
1. **Algo que o operador POSSUI:** CPF (identificador funcional único).
2. **Algo que o operador SABE:** Senha pessoal.
3. **Algo que o operador É:** Biometria Facial (frame capturado pela webcam).

O CPF localiza o vetor de referência previamente cadastrado no banco, permitindo realizar uma **Verificação 1:1** de alta velocidade e precisão (calculando a Distância Euclidiana em R^128). Cada falha de senha ou reconhecimento facial consome uma tentativa. Após **5 tentativas consecutivas falhas**, o sistema bloqueia o acesso preventivamente (`403 Forbidden`).

* **Método:** `POST`
* **Rota:** `/autenticar`
* **Autenticação:** Não necessária (Pública)

#### Headers da Requisição
```http
Content-Type: application/json
Accept: application/json
```

#### Corpo da Requisição (Request Body)
```json
{
  "cpf": "123.456.789-09",
  "senha": "Faca@2026",
  "imagem_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP..."
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|:---:|:---:|---|
| `cpf` | `string` | **Sim** | CPF do servidor com ou sem máscara (11 dígitos). |
| `senha` | `string` | **Sim** | Senha pessoal de acesso do operador. |
| `imagem_base64` | `string` | **Sim** | Frame capturado da webcam em Base64 (JPEG ou PNG). Data URL é tolerado e sanitizado. |

---

#### Resposta de Sucesso (`200 OK`)
Ocorre quando as credenciais (CPF + Senha) são válidas e exatamente um rosto é detectado e verificado com distância euclidiana menor ou igual à tolerância estipulada (padrão `0.50`).

```json
{
  "sucesso": true,
  "mensagem": "Autenticação multifator concluída com sucesso.",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibm9tZSI6Ikd1aWxoZXJtZSIsIm5pdmVsIjoxfQ.mock_signature_hash",
  "token_tipo": "Bearer",
  "expira_em_segundos": 28800,
  "usuario": {
    "id": 1,
    "nome": "Guilherme Ferreira",
    "matricula": "G9483B2",
    "cargo": "Engenheiro de Bioproteção",
    "divisao": "Divisão de Contenção Microbiológica",
    "nivel_acesso": 1
  },
  "biometria": {
    "reconhecido": true,
    "distancia_euclidiana": 0.3412,
    "tolerancia": 0.5,
    "confianca_percentual": 93.87
  }
}
```

> 📌 **Ação do Frontend:** Armazenar `token` e `usuario` no `sessionStorage` para injetar nas chamadas subsequentes e controlar o layout de acordo com `nivel_acesso`.

---

#### Respostas de Erro Mapeadas

##### 1. Erros de Captura Facial (`400 Bad Request`)
*Não consomem tentativas de login*, pois decorrem de problemas de posicionamento ou iluminação:

* **Nenhum rosto detectado (`NO_FACE_DETECTED`):**
  ```json
  {
    "sucesso": false,
    "erro": {
      "codigo": "NO_FACE_DETECTED",
      "mensagem": "Nenhum rosto foi detectado na imagem. Centralize seu rosto no enquadramento e certifique-se de estar em um ambiente iluminado.",
      "detalhes": { "rostos_encontrados": 0 }
    }
  }
  ```

* **Múltiplos rostos no enquadramento (`MULTIPLE_FACES_DETECTED`):**
  ```json
  {
    "sucesso": false,
    "erro": {
      "codigo": "MULTIPLE_FACES_DETECTED",
      "mensagem": "Múltiplos rostos detectados (2). Por motivos de segurança, apenas uma pessoa deve estar visível para a autenticação.",
      "detalhes": { "rostos_encontrados": 2 }
    }
  }
  ```

* **Imagem Base64 corrompida ou vazia (`INVALID_IMAGE`):**
  ```json
  {
    "sucesso": false,
    "erro": {
      "codigo": "INVALID_IMAGE",
      "mensagem": "A imagem enviada é inválida, corrompida ou está vazia.",
      "detalhes": null
    }
  }
  ```

##### 2. Falhas de Autenticação com Tentativas Restantes (`401 Unauthorized`)
Consomem uma tentativa. Informam `tentativas_restantes` para alertar o operador na interface:

* **Credenciais inválidas (`INVALID_CREDENTIALS`):**
  ```json
  {
    "sucesso": false,
    "bloqueado": false,
    "tentativas_restantes": 4,
    "tentativas_maximas": 5,
    "erro": {
      "codigo": "INVALID_CREDENTIALS",
      "mensagem": "CPF ou senha inválidos.",
      "detalhes": null
    }
  }
  ```

* **Rosto não reconhecido / Divergência Biométrica (`FACE_NOT_RECOGNIZED`):**
  ```json
  {
    "sucesso": false,
    "bloqueado": false,
    "tentativas_restantes": 3,
    "tentativas_maximas": 5,
    "erro": {
      "codigo": "FACE_NOT_RECOGNIZED",
      "mensagem": "Acesso Negado: a biometria facial não corresponde ao usuário informado.",
      "detalhes": {
        "reconhecido": false,
        "distancia_euclidiana": 0.7231,
        "tolerancia": 0.5,
        "confianca_percentual": 27.7
      }
    }
  }
  ```

##### 3. Bloqueio de Segurança por Suspeita de Ameaça (`403 Forbidden`)
Disparado imediatamente após **5 falhas consecutivas**:

```json
{
  "sucesso": false,
  "bloqueado": true,
  "tentativas_restantes": 0,
  "bloqueado_ate": "2026-10-19T04:45:00Z",
  "erro": {
    "codigo": "ACCOUNT_LOCKED",
    "mensagem": "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de autenticação malsucedidas. A ocorrência foi registrada e a equipe de segurança do cofre foi notificada.",
    "detalhes": {
      "tentativas_falhas": 5
    }
  }
}
```

---

### 4.3. Cadastro de Usuário e Biometria de Referência

Permite registrar um novo servidor público no sistema, vinculando seus dados funcionais, credenciais de acesso (CPF e senha) e o descritor biométrico de 128 dimensões extraído da foto facial de alta qualidade (Fases 1 a 4 do PIVC).

* **Método:** `POST`
* **Rota:** `/cadastrar`
* **Autenticação:** Não necessária para PoC inicial

#### Corpo da Requisição (Request Body)
```json
{
  "nome": "Júlia Fernandes",
  "cpf": "987.654.321-00",
  "senha": "Faca@2026",
  "matricula": "R101BF1",
  "cargo_id": 2,
  "divisao_id": 1,
  "nivel_acesso": 2,
  "imagem_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP..."
}
```

| Campo | Tipo | Obrigatório | Descrição |
|---|:---:|:---:|---|
| `nome` | `string` | **Sim** | Nome completo do indivíduo (mínimo 3 caracteres). |
| `cpf` | `string` | **Sim** | CPF com ou sem máscara (11 dígitos, único no sistema). |
| `senha` | `string` | **Sim** | Senha inicial (mínimo 8 caracteres, salva com hash criptográfico). |
| `matricula` | `string` | **Sim** | Identificador funcional / RA institucional (único). |
| `cargo_id` | `integer` | **Sim** | ID de referência do cargo no banco de dados. |
| `divisao_id` | `integer` | **Sim** | ID de referência da divisão governamental. |
| `nivel_acesso`| `integer` | **Sim** | Nível de permissão RBAC: `1` (Geral), `2` (Diretoria) ou `3` (Ministro). |
| `imagem_base64` | `string` | **Sim** | Foto de referência nítida da face para extração do vetor 128D. |

---

#### Resposta de Sucesso (`201 Created`)
```json
{
  "sucesso": true,
  "mensagem": "Usuário e biometria facial cadastrados com sucesso.",
  "usuario": {
    "id": 2,
    "nome": "Júlia Fernandes",
    "cpf_mascarado": "***.654.321-**",
    "matricula": "R101BF1",
    "cargo_id": 2,
    "divisao_id": 1,
    "nivel_acesso": 2,
    "criado_em": "2026-09-06T20:55:00Z"
  }
}
```

#### Respostas de Erro Esperadas
* **`400 Bad Request`:** Se a foto de cadastro não possuir exatamente 1 rosto válido (`NO_FACE_DETECTED` ou `MULTIPLE_FACES_DETECTED`).
* **`409 Conflict`:** Se o `cpf` ou a `matricula` já estiverem em uso no sistema (`CPF_ALREADY_EXISTS` ou `MATRICULA_ALREADY_EXISTS`).

---

### 4.4. Cofre de Toxinas (Rota Protegida / RBAC)

Recurso restrito do Ministério do Meio Ambiente. Retorna a listagem dos dados confidenciais do cofre. O servidor extrai a identidade e o `nivel_acesso` diretamente do token JWT enviado no cabeçalho `Authorization` e **filtra os registros retornados**.

* **Método:** `GET`
* **Rota:** `/toxinas`
* **Autenticação:** **Obrigatória** via Bearer Token

#### Headers da Requisição
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

---

#### Comportamento do Filtro Dinâmico por Nível de Acesso

1. **Usuário Nível 1 (Geral):**
   * Visualiza somente toxinas com `nivel_requerido: 1`.
   * Campos altamente sigilosos (como `protocolo_neutralizacao_critico` ou `codigo_estocagem_cofre`) são omitidos ou vêm com `null`.
2. **Usuário Nível 2 (Diretores de Divisão):**
   * Visualiza toxinas de `nivel_requerido: 1` e `nivel_requerido: 2`.
3. **Usuário Nível 3 (Ministro do Meio Ambiente):**
   * Acesso irrestrito a todos os espécimes (níveis 1, 2 e 3), incluindo armas químicas letais de destruição em massa e antídotos em fase confidencial.

---

#### Respostas de Sucesso (`200 OK`)

##### Exemplo de Retorno para Usuário de Nível 1:
```json
{
  "sucesso": true,
  "usuario_solicitante": {
    "nome": "Guilherme Ferreira",
    "nivel_acesso": 1
  },
  "total_registros": 1,
  "itens": [
    {
      "id": 101,
      "nome_comum": "Toxina Botulínica (Amostra Controle)",
      "codigo_amostra": "TOX-L1-004",
      "formula_molecular": "C6760H10447N1743O2010S32",
      "nivel_requerido": 1,
      "classificacao_risco": "Moderado / Monitorado",
      "temperatura_armazenamento_celsius": 4.0,
      "status_contenção": "Estável",
      "detalhes_confidenciais": null
    }
  ]
}
```

##### Exemplo de Retorno para Usuário de Nível 3 (Ministro):
```json
{
  "sucesso": true,
  "usuario_solicitante": {
    "nome": "Ministro do Meio Ambiente",
    "nivel_acesso": 3
  },
  "total_registros": 3,
  "itens": [
    {
      "id": 101,
      "nome_comum": "Toxina Botulínica (Amostra Controle)",
      "codigo_amostra": "TOX-L1-004",
      "formula_molecular": "C6760H10447N1743O2010S32",
      "nivel_requerido": 1,
      "classificacao_risco": "Moderado / Monitorado",
      "temperatura_armazenamento_celsius": 4.0,
      "status_contenção": "Estável",
      "detalhes_confidenciais": {
        "local_estocagem": "Cofre Criogênico A-01",
        "protocolo_neutralizacao": "Autoclave 121°C por 30min ou solução de hipoclorito a 0.5%"
      }
    },
    {
      "id": 204,
      "nome_comum": "Saxitoxina Sintetizada",
      "codigo_amostra": "TOX-L2-019",
      "formula_molecular": "C10H17N7O4",
      "nivel_requerido": 2,
      "classificacao_risco": "Crítico / Neurotoxina",
      "temperatura_armazenamento_celsius": -20.0,
      "status_contenção": "Estável",
      "detalhes_confidenciais": {
        "local_estocagem": "Cofre Subterrâneo B-12",
        "protocolo_neutralizacao": "Agentes alcalinos sob agitação contínua"
      }
    },
    {
      "id": 309,
      "nome_comum": "Quimera Biológica FX-99 (Agente Letal Nível 4)",
      "codigo_amostra": "TOX-L3-TOPSECRET",
      "formula_molecular": "Classificada - Gabinete Ministerial",
      "nivel_requerido": 3,
      "classificacao_risco": "Catastrófico Global",
      "temperatura_armazenamento_celsius": -80.0,
      "status_contenção": "Alerta Máximo / Bloqueio Ativo",
      "detalhes_confidenciais": {
        "local_estocagem": "Câmara de Vácuo Central - Cofre Omega",
        "protocolo_neutralizacao": "Incinerador de plasma de alta temperatura acionado por chave dupla"
      }
    }
  ]
}
```

---

#### Respostas de Erro da Rota Protegida

##### 1. Token Ausente ou Inválido (`401 Unauthorized`)
```json
{
  "sucesso": false,
  "erro": {
    "codigo": "TOKEN_INVALID_OR_EXPIRED",
    "mensagem": "Token de autorização não fornecido, inválido ou expirado."
  }
}
```

##### 2. Acesso Negado / Permissão Insuficiente (`403 Forbidden`)
Caso o endpoint venha a ser configurado para bloquear totalmente uma sub-rota (ex: `/toxinas/{id}` restrito):
```json
{
  "sucesso": false,
  "erro": {
    "codigo": "INSUFFICIENT_PRIVILEGES",
    "mensagem": "Seu nível de acesso (1) não tem permissão para visualizar o recurso solicitado."
  }
}
```

---

### 4.5. Rotas de Diagnóstico e Validação do PIVC (Sem Dependência de Banco)

Endpoints técnicos sob a tag `Visão Computacional (PIVC)` para testes imediatos das 5 fases do Processamento Digital de Imagens via Swagger (`/docs`), sem necessidade de banco de dados populado:

#### 4.5.1. Status do Motor Biométrico (`GET /biometria/status`)
Informa a disponibilidade dos bindings C++ da biblioteca dlib / `face_recognition` e os hiperparâmetros carregados do ambiente (`FACE_RECOGNITION_TOLERANCE`, dimensões máximas, modelo HOG).

```json
{
  "motor_disponivel": true,
  "tolerancia": 0.5,
  "modelo_deteccao": "hog",
  "upsample": 1,
  "dimensao_maxima_px": 800,
  "dimensao_vetor": 128
}
```

#### 4.5.2. Extração de Vetor 128D — Fases 1 a 4 (`POST /biometria/extrair-vetor`)
Executa o pipeline de aquisição, pré-processamento, segmentação facial (HOG) e extração de características profundas (ResNet-34 do dlib), retornando o vetor numérico, a localização do rosto e a telemetria de latência por fase:

* **Payload:**
  ```json
  {
    "imagem_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP...",
    "num_jitters": 1
  }
  ```

* **Resposta (`200 OK`):**
  ```json
  {
    "sucesso": true,
    "mensagem": "Vetor biométrico 128D extraído com sucesso.",
    "rosto_detectado": true,
    "quantidade_rostos": 1,
    "localizacao_rosto": {
      "top": 112,
      "right": 418,
      "bottom": 341,
      "left": 189
    },
    "dimensoes_originais": { "largura": 1280, "altura": 720 },
    "dimensoes_processadas": { "largura": 800, "altura": 450 },
    "fator_escala": 0.625,
    "iluminacao_normalizada": false,
    "dimensao_vetor": 128,
    "vetor_caracteristicas": [-0.1234, 0.0543, "... 128 floats ..."],
    "tempos_fases_ms": {
      "fase1_aquisicao": 4.1,
      "fase2_preprocessamento": 2.3,
      "fase3_segmentacao": 182.5,
      "fase4_extracao": 61.7
    },
    "tempo_total_ms": 250.6
  }
  ```

#### 4.5.3. Comparação 1:1 Direta entre Duas Imagens — Fases 1 a 5 (`POST /biometria/comparar-teste`)
Compara duas imagens Base64 puramente em memória, retornando a Distância Euclidiana ($d = \Vert\vec{v}_1 - \vec{v}_2\Vert_2$) e se houve correspondência segundo a tolerância:

* **Payload:**
  ```json
  {
    "imagem_referencia_base64": "/9j/4AAQSkZJRg...",
    "imagem_teste_base64": "/9j/4AAQSkZJRg...",
    "tolerancia": 0.5
  }
  ```

* **Resposta (`200 OK`):**
  ```json
  {
    "sucesso": true,
    "mensagem": "As faces pertencem à mesma pessoa (match biométrico confirmado).",
    "resultado": {
      "reconhecido": true,
      "distancia_euclidiana": 0.3124,
      "tolerancia": 0.5,
      "confianca_percentual": 95.12
    },
    "localizacao_rosto_referencia": { "top": 98, "right": 390, "bottom": 320, "left": 170 },
    "localizacao_rosto_teste": { "top": 105, "right": 402, "bottom": 331, "left": 180 },
    "tempo_total_ms": 482.3
  }
  ```

#### 4.5.4. Verificação Imagem × Vetor 128D (`POST /biometria/verificar-vetor`)
Simula a verificação biométrica exata utilizada pelo cofre contra o vetor previamente salvo:

* **Payload:**
  ```json
  {
    "imagem_base64": "/9j/4AAQSkZJRg...",
    "vetor_referencia": [-0.1234, 0.0543, "... 128 floats ..."],
    "tolerancia": 0.5
  }
  ```

* **Resposta (`200 OK`):**
  ```json
  {
    "sucesso": true,
    "mensagem": "Biometria compatível com o vetor de referência.",
    "resultado": {
      "reconhecido": true,
      "distancia_euclidiana": 0.3412,
      "tolerancia": 0.5,
      "confianca_percentual": 93.87
    },
    "tempo_total_ms": 251.3
  }
  ```

---

## 5. Exemplos de Implementação Frontend (`fetch` em JavaScript)

Abaixo estão exemplos prontos para copiar e adaptar na camada de serviços do Frontend (`api.js`).

### 5.1. Serviço Central de Requisições (`api.js`)

```javascript
// Configuração da URL base
const API_BASE_URL = 'http://localhost:8000';

/**
 * 1. Testar se a API está online
 */
export async function testarConexao() {
  try {
    const resposta = await fetch(`${API_BASE_URL}/ping`);
    if (!resposta.ok) throw new Error('API indisponível');
    return await resposta.json();
  } catch (erro) {
    console.error('Falha no Health Check:', erro);
    throw erro;
  }
}

/**
 * 2. Enviar imagem Base64 para autenticação facial
 * @param {string} base64Puro - Imagem sem o prefixo data:image/...
 */
export async function autenticarBiometria(base64Puro) {
  const resposta = await fetch(`${API_BASE_URL}/autenticar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify({ imagem_base64: base64Puro })
  });

  const dados = await resposta.json();

  if (!resposta.ok) {
    // Tratar os erros de negócio (400, 401, etc.)
    const codigoErro = dados.erro?.codigo || 'UNKNOWN_ERROR';
    const mensagem = dados.erro?.mensagem || 'Erro ao autenticar.';
    throw { status: resposta.status, codigo: codigoErro, mensagem };
  }

  // Sucesso: guardar dados no storage
  sessionStorage.setItem('faca_token', dados.token);
  sessionStorage.setItem('faca_usuario', JSON.stringify(dados.usuario));

  return dados;
}

/**
 * 3. Consultar o cofre de toxinas (Rota Protegida)
 */
export async function listarToxinas() {
  const token = sessionStorage.getItem('faca_token');

  if (!token) {
    throw new Error('Usuário não autenticado. Redirecionando para login...');
  }

  const resposta = await fetch(`${API_BASE_URL}/toxinas`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    }
  });

  if (resposta.status === 401) {
    // Token expirou ou foi invalidado
    sessionStorage.clear();
    window.location.href = '/login.html';
    throw new Error('Sessão expirada. Faça login novamente.');
  }

  const dados = await resposta.json();
  return dados;
}

/**
 * 4. Cadastrar novo usuário e face de referência
 */
export async function cadastrarUsuario(dadosFormulario, base64Puro) {
  const payload = {
    nome: dadosFormulario.nome,
    matricula: dadosFormulario.matricula,
    cargo_id: Number(dadosFormulario.cargo_id),
    divisao_id: Number(dadosFormulario.divisao_id),
    nivel_acesso: Number(dadosFormulario.nivel_acesso),
    imagem_base64: base64Puro
  };

  const resposta = await fetch(`${API_BASE_URL}/cadastrar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw {
      status: resposta.status,
      codigo: dados.erro?.codigo || 'CADASTRO_FAILED',
      mensagem: dados.erro?.mensagem || 'Falha ao realizar cadastro.'
    };
  }

  return dados;
}
```

### 5.2. Exemplo de Captura de Vídeo e Tratamento de Erros no Frontend

```javascript
async function handleDispararAutenticacao() {
  const videoElement = document.getElementById('camera-preview');
  const canvasElement = document.getElementById('camera-snapshot');
  const statusElement = document.getElementById('feedback-msg');

  // Desenha o frame do vídeo no canvas
  const ctx = canvasElement.getContext('2d');
  canvasElement.width = videoElement.videoWidth;
  canvasElement.height = videoElement.videoHeight;
  ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

  // Extrai o Base64 limpo (sem prefixo)
  const base64Limpo = canvasElement
    .toDataURL('image/jpeg', 0.9)
    .replace(/^data:image\/[a-z]+;base64,/, '');

  try {
    statusElement.innerText = 'Processando biometria...';
    const resultado = await autenticarBiometria(base64Limpo);

    statusElement.innerText = `Bem-vindo(a), ${resultado.usuario.nome}! Acesso Nível ${resultado.usuario.nivel_acesso} concedido.`;
    
    // Redireciona para o cofre
    setTimeout(() => {
      window.location.href = '/cofre.html';
    }, 1200);

  } catch (erro) {
    // Tratamento individualizado por código de erro
    switch (erro.codigo) {
      case 'NO_FACE_DETECTED':
        statusElement.className = 'aviso-alerta';
        statusElement.innerText = '⚠️ Nenhum rosto encontrado. Enquadre-se melhor.';
        break;
      case 'MULTIPLE_FACES_DETECTED':
        statusElement.className = 'aviso-alerta';
        statusElement.innerText = '⚠️ Múltiplas pessoas na câmera. Apenas 1 pessoa por vez.';
        break;
      case 'FACE_NOT_RECOGNIZED':
        statusElement.className = 'aviso-perigo';
        statusElement.innerText = '❌ Rosto não cadastrado. Acesso negado!';
        break;
      default:
        statusElement.className = 'aviso-perigo';
        statusElement.innerText = `❌ Erro: ${erro.mensagem}`;
    }
  }
}
```

---

## 6. Dúvidas Frequentes e Suporte Interno

* **P: A imagem pode ser enviada em PNG ou somente JPEG?**  
  **R:** Ambas são aceitas pelo backend, desde que a string Base64 não contenha o prefixo `data:image/...`. O formato JPEG com compressão `0.85` ou `0.9` é preferível para manter a requisição leve e veloz.
* **P: Quanto tempo o token de autenticação permanece válido?**  
  **R:** 8 horas (`expira_em_segundos: 28800`).
* **P: O que acontece se o usuário tentar alterar seu `nivel_acesso` no LocalStorage?**  
  **R:** A tela pode até alterar visualmente no cliente, mas qualquer chamada à rota `/toxinas` terá sua autorização conferida pelo backend com base na assinatura criptográfica do token JWT. Se a assinatura não bater ou os privilégios forem insuficientes, o backend não enviará os dados.
