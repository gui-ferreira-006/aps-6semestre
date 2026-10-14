# Relatório de Desenvolvimento do Frontend — F.A.C.A

**Projeto:** F.A.C.A - Frente de Autenticação e Controle de Acesso  
**Instituição:** Ministério do Meio Ambiente / UNIP - APS 6° Semestre  
**Responsável Frontend:** Júlia Fernandes  
**Data:** 13/10/2026  

---

## 📌 Enquadramento no ROADMAP

Este pacote de entregas se enquadra principalmente na:

### 🎯 **Etapa 6 — Telas Web e Integração** (Aba Principal)
- **Status atual no Roadmap:** Em Andamento / Frontend Base Concluído.
- **O que cobre:** Desenvolvimento completo da interface visual, estilização com estética militar/cyber security, componentes de entrada, animações e fluxo sequencial entre telas (Login ➔ Biometria Facial).

### 🔗 **Etapa 4 — Prova de Conceito (Captura de Vídeo)** (Aba Correlata)
- **O que cobre:** Implementação do módulo de aquisição de vídeo via WebRTC (`getUserMedia`), alternador entre malha simulada e câmera real, além da retícula HUD sobreposta ao vídeo.

---

## 📋 Resumo de Tudo o que Foi Implementado

### 1. Estrutura e Interface Principal (`index.html`)
- **Cabeçalho Institucional F.A.C.A:**
  - Emblema vetorial (SVG) com escudo poligonal metálico, conexões de circuito eletrônico e núcleo central avermelhado com cadeado de alta segurança.
  - Tipografia de alta precisão com os títulos `F.A.C.A` e `MINISTÉRIO DO MEIO AMBIENTE`.
- **Anotações de HUD nos Quatro Cantos da Tela:**
  - *Superior Esquerdo:* `SEGURANÇA / INFORMAÇÃO / PRESERVAÇÃO / UM FUTURO MAIS SEGURO`.
  - *Superior Direito:* `ACESSO RESTRITO` com indicador de linha laser.
  - *Inferior Esquerdo:* `TECNOLOGIA A SERVIÇO DA CONSERVAÇÃO`.
  - *Inferior Direito:* Marcador em formato de estrela e `NATUREZA / DADOS / RESULTADOS`.
- **Nomenclatura 100% em PT-BR** para todos os arquivos e componentes do projeto.

---

### 2. Fluxo Sequencial de Autenticação (Login ➔ Leitura Biométrica)

Ao invés de exibir os dois formulários lado a lado, foi criado um sistema em etapas (*step-by-step*):

#### **Etapa 1: Acesso por CPF e Senha**
- **Card de Autenticação:** Painel translúcido escuro em *glassmorphism* com bordas finas e iluminação avermelhada.
- **Campo de CPF:**
  - Ícone de identificação.
  - Máscara dinâmica inteligente: aplica formatação padrão `000.000.000-00` ao digitar números, mas aceita dados de teste para agilidade.
- **Campo de Senha:**
  - Ícone de cadeado.
  - Botão interativo para alternar visualização da senha (ícone de olho aberto / fechado).
- **Botão ENTRAR →:**
  - Botão carmim com efeito de brilho e elevação no hover.
  - Disparo de validação e transição animada.
  - Modo de teste rápido: preenche dados de demonstração automaticamente caso os campos estejam vazios ao clicar em Entrar.
- **Link Secundário:** *"Esqueceu sua senha?"* com mensagem de feedback contextual.

#### **Etapa 2: Reconhecimento Facial (Biometria)**
- **Transição Suave:** Animação em CSS com fade e escala alternando entre as seções.
- **Visor do Scanner Facial:**
  - 4 retículas angulares nos cantos (`[ ]`).
  - Mira cartesiana sutil (linhas horizontal e vertical).
  - Linha laser vermelha com animação de varredura vertical contínua.
- **Malha Holográfica 3D (`scanner-facial.js`):**
  - Renderização em tempo real de uma malha facial tridimensional realista (topologia com crânio, sobrancelhas, olhos, nariz, lábios, queixo e maçãs do rosto).
  - Rotação oscilatória suave e nós luminosos pulsantes.
  - Rastreamento dos olhos com mira pontilhada vermelha.
- **Varredura e Leitura Biométrica:**
  - Botão **INICIAR RECONHECIMENTO** que aciona o processo de escaneamento.
  - Barra de progresso com gradiente e contador percentual HUD (`0%` até `100%`).
  - Resposta de autorização de segurança: *"ACESSO LIBERADO: Nível 2 - Divisão de Toxinas e Preservação"*.
- **Integração com Câmera Real:**
  - Botão *"Ativar Câmera Real"* para capturar o stream ao vivo da webcam do usuário mantendo os efeitos de HUD sobrepostos.
- **Navegação de Retorno:**
  - Botão *"← Voltar para identificação"* para retornar ao formulário inicial a qualquer momento.

---

### 3. Efeitos Visuais e Interatividade Avançada

- **Rede Neural de Fundo (`particulas.js`):**
  - Animação matemática contínua em Canvas com dezenas de partículas avermelhadas conectadas por linhas cinéticas dinâmicas.
  - Reação de repulsão magnética sutil ao movimento do cursor do mouse.
  - Redimensionamento automático de acordo com a resolução da janela (*responsive canvas*).
- **Folha de Estilos (`estilo.css`):**
  - Sistema de variáveis CSS (`--red-primary`, `--card-bg`, etc.).
  - Efeitos de profundidade, sombras volumétricas e desfoque de fundo (`backdrop-filter`).
  - Responsividade completa para dispositivos móveis e monitores ultrawide.

---

## 📂 Mapa de Arquivos Gerados (em PT-BR)

| Arquivo | Localização | Descrição |
|---|---|---|
| `index.html` | `/index.html` | Estrutura principal da página, cabeçalhos, formulários e visores |
| `estilo.css` | `/src/css/estilo.css` | Folha de estilos, temas, cores, tipografia e animações |
| `principal.js` | `/src/js/principal.js` | Controle de estados, validações, alternância de etapas e transições |
| `scanner-facial.js` | `/src/js/scanner-facial.js` | Renderizador da malha 3D facial, HUD de biometria e controle de câmera |
| `particulas.js` | `/src/js/particulas.js` | Rede neural animada de fundo com partículas conectadas |

---

## 🚀 Como Executar e Testar

1. Basta abrir o arquivo `index.html` em qualquer navegador web moderno (Chrome, Edge, Firefox).
2. Na tela de login, clique em **ENTRAR →** (com ou sem preenchimento dos campos).
3. Na tela de biometria, clique em **INICIAR RECONHECIMENTO** ou em **Ativar Câmera Real** para testar a webcam.
