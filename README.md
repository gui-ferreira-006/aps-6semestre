# F.A.C.A - Frente de Autenticação e Controle de Acesso/ APS 6° Semestre

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

> 🔐 **Sistema de Identificação e Autenticação Biométrica**
> Ciência da Computação · UNIP · 2026/2

---

## 1. Informações Gerais

| Item | Detalhe |
|---|---|
| **Curso** | Ciência da Computação — 6º Semestre |
| **Semestre** | 2026/2 |
| **Disciplina base** | Processamento de Imagem e Visão Computacional (PIVC) |
| **Tema oficial** | Frente de Autenticação e Controle de Acesso - F.A.C.A. |

### 👥 Equipe

| Integrante | RA | Responsabilidade |
|---|---|---|
| Guilherme | G9483B2 | Backend, Visão Computacional & Infraestrutura |
| Júlia Fernandes | R101BF1 | Frontend/Documentação |
| Felipe | R079CB0 | Banco de Dados/Documentação |

---

## 2. Visão Geral do Projeto

Sistema de segurança por **reconhecimento facial** para um cofre de segurança máxima do **Ministério do Meio Ambiente**.

O cofre guarda informações sobre toxinas perigosas capazes de causar uma catástrofe global. O sistema é a **última linha de defesa**: só libera o acesso após validar o rosto da pessoa em tempo real.

---

## 3. Objetivos e Regras de Negócio

**Objetivo geral:** criar um sistema **Web** robusto de autenticação biométrica com reconhecimento facial em tempo real.

### 🎚️ Níveis de acesso

| Nível | Quem tem acesso |
|:---:|---|
| **1** | Indivíduos com permissão geral |
| **2** | Diretores de divisões específicas |
| **3** | Exclusivo do Ministro do Meio Ambiente |

### 🧪 Requisito técnico obrigatório

O processamento da imagem **precisa** passar pelas 5 fases do processamento de imagens digitais:

1. **Aquisição** — sensor / câmera
2. **Pré-processamento**
3. **Segmentação**
4. **Extração de características**
5. **Classificação e interpretação**

---

## 4. Arquitetura e Tecnologias

Todas as escolhas estão dentro das opções permitidas pelo manual.

| Camada | Tecnologia |
|---|---|
| **Frontend** (captura de imagem) | HTML, CSS, JavaScript (Vanilla ou TensorFlow.js) |
| **Backend** (motor biométrico e API) | Python |
| **Visão Computacional** | OpenCV |
| **Banco de Dados** | MySQL — credenciais, hashes, nível de acesso e vetores faciais |
| **Banco de Dados (local/testes)** | SQLite |
| **Infraestrutura** | Docker (containerização) |

> ❓ **Confirmar com o orientador:** se o Docker substitui o uso sugerido de XAMPP/Apache.

---

## 5. Trabalho Escrito (Dissertação) — 70% da nota

### 📐 Formatação obrigatória

- Fonte **Arial 12**
- Espaçamento **1,5**
- Margens **2,5 cm**
- Papel **A4**
- Encadernação em **espiral com capa transparente**

### 📑 Estrutura e limite de páginas

| # | Seção | Páginas |
|:--:|---|:--:|
| 1 | Capa (curso, tema, relação de alunos com Nome/RA) | — |
| 2 | Índice | — |
| 3 | Objetivo e motivação do trabalho | 1 a 2 |
| 4 | Introdução | 2 a 8 |
| 5 | Fundamentos das principais técnicas (Reconhecimento Facial) | 10 a 20 |
| 6 | Plano de desenvolvimento da aplicação | 5 a 15 |
| 7 | Projeto (estrutura e módulos) do programa | 18 a 35 |
| 8 | Relatório de Código (linhas de código do programa) | — |
| 9 | Bibliografia | — |
| 10 | Ficha de Atividades Práticas Supervisionadas | — |

**Observações por seção:**

- **Seção 5** → pesquisar OpenCV, Redes Neurais, Haar Cascades, LBPH etc.
- **Seção 6** → ferramentas e elementos usados.
- **Seção 7** → diagramas do banco, arquitetura da API e as 5 fases do processamento aplicadas na prática.
- **Seção 8** → modelo disponibilizado no Teams.

> 💡 **Não esquecer:** o documento precisa discutir a **interdisciplinaridade** — como Banco de Dados, Redes/Web, Cálculo Numérico e PIVC se integram no projeto.

---

## 6. Cronograma e Prazos

| Etapa | Prazo |
|---|---|
| Montagem do grupo | até **12/11/2026** |
| Postagem do trabalho (site UNIP) | **13/10/2026 a 12/11/2026** |
| Entregas parciais (Microsoft Teams) | a combinar com o orientador |
| Apresentação final | **30% da nota** |

**Apresentação final:** mostrar o programa rodando em um computador, provando todas as funcionalidades, funções extras e tratamento de erros.

---

## ✅ Pendências

- [x] Definir a área do Felipe
- [ ] Confirmar Docker x XAMPP/Apache com o orientador
- [ ] Combinar datas das entregas parciais no Teams
- [x] Coletar os RAs de Guilherme e Felipe para a capa
