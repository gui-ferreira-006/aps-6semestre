# Walkthrough Arquitetural: Motor Biométrico e Contêinerização — F.A.C.A.

> **APS 6º Semestre — UNIP 2026/2**  
> **Tema:** Frente de Autenticação e Controle de Acesso (F.A.C.A.)  
> **Disciplina Principal:** Processamento de Imagem e Visão Computacional (PIVC)

---

## 1. Contexto e Objetivo do Documento

O projeto **F.A.C.A.** foi concebido como a linha de defesa física e digital para proteção do cofre de segurança máxima do **Ministério do Meio Ambiente**, responsável pela guarda de amostras biológicas e toxinas de alto risco.

Este documento apresenta uma visão conceitual e direta sobre dois dos pilares estruturais mais importantes do projeto:
1. **O Motor Biométrico Facial** ([`biometria.py`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py)), que operacionaliza os fundamentos de Processamento de Imagem e Visão Computacional (PIVC);
2. **A Contêinerização e Orquestração** ([`Dockerfile`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/Dockerfile) e [`docker-compose.yml`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/docker-compose.yml)), que viabiliza a execução consistente da aplicação integrada ao banco de dados relacional MySQL 8.0.

---

## 2. Motor Biométrico ([`biometria.py`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py))

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PIPELINE BIOMÉTRICO PIVC                        │
│                                                                        │
│  [Webcam] ──▶ 1. Aquisição       (Base64 ➔ Matriz BGR)                 │
│                     │                                                  │
│                     ▼                                                  │
│               2. Pré-processam.  (Downscale, CLAHE condicional, RGB)   │
│                     │                                                  │
│                     ▼                                                  │
│               3. Segmentação     (Detecção HOG / Trava de face única)  │
│                     │                                                  │
│                     ▼                                                  │
│               4. Extração        (ResNet-34 ➔ Vetor numérico 128D)     │
│                     │                                                  │
│                     ▼                                                  │
│               5. Classificação   (Distância Euclidiana vs. MySQL)      │
│                     │                                                  │
│                     ▼                                                  │
│            [Decisão: MATCH / ACESSO NEGADO]                            │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1. Como é aplicado na arquitetura

O motor biométrico é um módulo em Python puro, **totalmente desacoplado de banco de dados e de protocolos web**. Ele opera em memória recebendo matrizes de imagem e devolvendo dados analíticos ou decisões de equivalência.

Sua arquitetura é dividida rigorosamente nas **cinco fases clássicas do PIVC**:

1. **[Fase 1: Aquisição](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L556-L658)** ([`fase1_aquisicao`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L599-L658)): Recebe o frame capturado pela câmera do operador em formato de texto Base64, sanitiza o conteúdo e o decodifica em uma matriz bidimensional de pixels coloridos (padrão BGR via OpenCV).
2. **[Fase 2: Pré-processamento](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L660-L754)** ([`fase2_preprocessamento`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L705-L754)): Padroniza a imagem para reduzir a latência e eliminar ruídos ambientais. Realiza o redimensionamento proporcional (downscaling), aplica equalização adaptativa de histograma (CLAHE no canal de luminância $L^*$ do espaço CIELAB) apenas quando o ambiente estiver mal iluminado, e converte as cores para RGB contíguo.
3. **[Fase 3: Segmentação](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L756-L811)** ([`fase3_segmentacao`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L774-L811)): Isola a face humana do cenário de fundo através do algoritmo HOG (*Histogram of Oriented Gradients*) acoplado a um classificador linear SVM, delimitando a Região de Interesse (ROI).
4. **[Fase 4: Extração de Características](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L813-L890)** ([`fase4_extracao_caracteristicas`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L852-L890)): Alinha a face a partir de 5 marcos anatômicos (olhos e nariz) e processa a imagem em uma rede neural profunda (ResNet-34). O resultado é uma representação matemática compacta: um **vetor numérico de 128 dimensões** que descreve unicamente os traços da pessoa.
5. **[Fase 5: Classificação e Tomada de Decisão](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L892-L970)** ([`fase5_classificacao`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L939-L970)): Realiza a comparação 1:1 calculando a **distância euclidiana** entre o vetor recém-extraído e o vetor de referência persistido no banco de dados. Caso a distância esteja dentro do limiar de segurança ($\le 0.50$), a identidade é confirmada; caso contrário, é rejeitada.

### 2.2. Pertinência no projeto

* **Segundo Fator de Autenticação (MFA):** O cofre armazena toxinas letais. A senha por si só (algo que o usuário sabe) é insuficiente; a biometria facial (algo que o usuário é) impede que credenciais vazadas ou furtadas autorizem acessos indevidos.
* **Salvaguarda de Face Única:** Na Fase 3, o sistema rejeita autenticações se detectar zero faces ou mais de uma face. Essa regra mitiga tentativas de coação (alguém forçando o operador) e a prática de "carona" (*tailgating*).
* **Cadastro Automatizado (*Enrollment On-the-Fly*):** O operador inicia sem biometria gravada; ao acertar sua credencial operacional pela primeira vez, o motor extrai seu vetor biométrico 128D e o vincula ao seu perfil sem fricção burocrática.
* **Isolamento de Erros:** O módulo gera exceções ricas ([`BiometriaError`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py#L169-L192)) com códigos legíveis pelo frontend (`NO_FACE_DETECTED`, `MULTIPLE_FACES_DETECTED`, `FACE_NOT_RECOGNIZED`), orientando o operador em tempo real.

---

## 3. Contêinerização e Banco de Dados ([`Dockerfile`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/Dockerfile) e [`docker-compose.yml`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/docker-compose.yml))

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ECOSSISTEMA DOCKER DO F.A.C.A.                    │
│                                                                        │
│                      Rede Isolada: faca_network                        │
│                                                                        │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │  Serviço: backend         │      │  Serviço: db                │   │
│   │  Container:               │      │  Container:                 │   │
│   │  faca_backend_api         │      │  faca_mysql_db              │   │
│   │                           │      │                             │   │
│   │  • Python 3.10-slim       │ TCP  │  • MySQL 8.0 Oficial        │   │
│   │  • OpenCV + dlib nativo   │─────▶│  • Charset: UTF8MB4         │   │
│   │  • FastAPI REST Engine    │:3306 │  • Health Check TCP         │   │
│   │  • Hot-reload de dev      │      │  • Auto-seed em ./database  │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
│                 │                                   │                  │
│   Porta :8000   │                     Porta :3307   │ Volume           │
│   (Host)        ▼                     (Host)        ▼ faca_mysql_data  │
└─────────────────┼───────────────────────────────────┼──────────────────┘
                  │                                   │
              Navegador /                         Persistência
            Terminal Desktop                       de Dados
```

### 3.1. Como é aplicado na arquitetura

A contêinerização foi estruturada para transformar a infraestrutura do sistema em código reproduzível:

1. **[`Dockerfile`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/Dockerfile) (Construção da API e Motor Biométrico):**
   * **Base Lean e Otimizada:** Utiliza `python:3.10-slim` para manter a imagem leve e veloz.
   * **Toolchain de Compilação Nativa:** Instala pacotes essenciais do sistema operacional (`cmake`, `build-essential`, `libopenblas-dev`, `liblapack-dev`). Esses compiladores são obrigatórios para construir os *bindings* em C++ do `dlib`, biblioteca fundamental de visão computacional.
   * **Aproveitamento de Cache de Camadas:** As dependências do Python em [`requirements.txt`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/requirements.txt) são instaladas antes da cópia do código-fonte, evitando reinstalações demoradas a cada alteração de código.

2. **[`docker-compose.yml`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/docker-compose.yml) (Orquestração Multisserviço):**
   * **Serviço de Banco (`db`):** Executa a imagem oficial do **MySQL 8.0**, ajustada para `utf8mb4` e persistida via volume nomeado (`faca_mysql_data`). Mapeia o diretório local [`./database`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/database) para `/docker-entrypoint-initdb.d`, executando automaticamente o esquema em 3FN ([`01_schema_base.sql`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/database/01_schema_base.sql)) e a carga de operadores/toxinas ([`02_seed_operadores_e_cofre.sql`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/database/02_seed_operadores_e_cofre.sql)) no primeiro boot.
   * **Serviço de Aplicação (`backend`):** Constrói a imagem local, conecta-se ao banco pelo hostname interno seguro `db:3306`, expõe a porta `8000` para consumo e habilita hot-reload com proteção contra poluição de arquivos do host (`.venv`, `__pycache__`).
   * **Rede Interna e Resiliência com Health Checks:** Uma rede privativa (`faca_network`) interliga os serviços. O backend só inicia após o MySQL emitir status saudável (`condition: service_healthy`), prevenindo falhas de inicialização ou conexões recusadas durante a subida do banco.

### 3.2. Pertinência no projeto

* **Eliminação do Problema "Na minha máquina funciona":** Bibliotecas de visão computacional como o `dlib` exigem ferramentas de compilação complexas que frequentemente quebram dependendo do sistema operacional do avaliador (Windows, macOS ou distribuições Linux). O contêiner garante que o ambiente seja 100% idêntico em qualquer máquina.
* **Provisionamento Automatizado e Imediato:** Com um único comando (`docker compose up -d`), todo o banco de dados é provisionado, o esquema é criado, os operadores de teste são inseridos e a API passa a responder sem necessidade de configuração manual de banco ou dependências.
* **Segurança e Isolamento:** O banco de dados opera em uma rede interna, aceitando consultas da aplicação diretamente pelo endereço de serviço, enquanto os dados ficam protegidos em volumes dedicados.

---

## 4. Integração Sistêmica: A Sinergia entre Biometria e Infraestrutura

A força do projeto está na forma como o motor biométrico e a infraestrutura contêinerizada conversam com as regras de negócio:

1. **Captura e Envio:** O operador posiciona-se em frente à câmera e informa suas credenciais na interface. O frame é enviado em Base64 para a rota `/autenticar`.
2. **Processamento no Contêiner Backend:** O serviço contêinerizado executa [`biometria.py`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py), decodifica o frame, trata a iluminação, segmenta o rosto e calcula o vetor de 128 dimensões.
3. **Consulta ao Banco MySQL:** O backend acessa a tabela `biometria` no contêiner MySQL via SQLAlchemy 2.0 ([`models.py`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/models.py)).
4. **Decisão e Controle de Acesso (RBAC):**
   * Se for o primeiro acesso, o vetor 128D é gravado como novo padrão do usuário (*enrollment*);
   * Se o usuário já possuir cadastro, o motor compara os vetores matematicamente. Havendo correspondência, o token de sessão é gerado com o respectivo nível de acesso (Nível 1, 2 ou 3), liberando as funções do cofre e registrando a tentativa na tabela de auditoria.

---

## 5. Resumo Conclusivo

* O **Motor Biométrico ([`biometria.py`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/biometria.py))** materializa o rigor da disciplina de Visão Computacional, oferecendo autenticação facial de alta precisão baseada em redes neurais e estruturada em cinco fases limpas e auditáveis.
* A **Contêinerização ([`Dockerfile`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/Dockerfile) e [`docker-compose.yml`](file:///c:/Users/Guilherme/Documents/APS/Semestres/6_semestre/aps-6semestre/docker-compose.yml))** assegura a viabilidade prática do projeto, empacotando uma pilha complexa de dependências C++ e banco relacional em uma infraestrutura moderna, reproduzível e resiliente.
