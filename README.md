# APS (Atividades Práticas Supervisionadas) 6

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

---

## 1. Informações Gerais

| Campo | Descrição |
|---|---|
| Curso | Ciência da Computação (6º Semestre) |
| Disciplina Base | Processamento de Imagens e Visão Computacional |
| Tema Norteador | Meio Ambiente e Sustentabilidade (Foco: Descarte de Lixo Eletrônico / E-waste) |

**Equipe**
- Guilherme
- Júlia

---

## 2. Visão Geral do Projeto

O projeto consiste no desenvolvimento de uma aplicação Web (localhost) voltada para o incentivo ao descarte correto de equipamentos eletrônicos. O sistema utilizará **reconhecimento e biometria facial** para autenticar os usuários em ecopontos ou estações de coleta. Ao realizar o descarte, o usuário é validado pela câmera e recebe uma pontuação ou benefícios em sua conta, garantindo um processo seguro, sem fraudes e totalmente automatizado (paperless/cardless).

---

## 3. Objetivos

**Objetivo Geral**

Desenvolver um sistema Web funcional de autenticação via biometria facial atrelado a um programa de benefícios para descarte de lixo eletrônico.

**Objetivos Específicos**

- Desenvolver uma interface Web responsiva (Frontend) para captura da imagem via webcam.
- Processar a imagem e extrair as características faciais usando bibliotecas de Visão Computacional em Python (Backend).
- Criar uma API (Backend) para orquestrar a comunicação entre o Frontend, o motor de biometria e a gestão da pontuação dos usuários.
- Modelar um banco de dados relacional para armazenar credenciais de usuários, hash de senhas, vetor biométrico e saldo de pontos.
- Empacotar toda a aplicação utilizando Docker para facilitar o deploy e a execução do ambiente.

---

## 4. Ideação e Justificativa (Descarte de Eletrônicos com Biometria)

**O Problema**

O descarte irregular de lixo eletrônico causa contaminação do solo e da água devido a metais pesados. Além disso, sistemas de recompensa tradicionais (com cartões ou senhas) são suscetíveis a fraudes ou esquecimentos.

**A Solução**

Uma estação de descarte onde o usuário se identifica apenas olhando para a câmera. O sistema reconhece a face (Visão Computacional), acessa o banco de dados e adiciona os "Eco-pontos" na conta do usuário, que podem ser trocados por benefícios futuramente. A biometria garante que a pessoa certa está recebendo os pontos, de forma higiênica (contactless) e rápida.

---

## 5. Divisão de Tarefas e Responsabilidades

### Guilherme — Backend, Visão Computacional & Infraestrutura (Docker)

- **Visão Computacional:** Implementar detecção e reconhecimento facial usando Python (OpenCV, face_recognition, etc.).
- **Desenvolvimento da API (Backend):** Desenvolver o servidor em Python (sugestão: FastAPI ou Flask) para receber a imagem, processar a autenticação e gerenciar a lógica de adição de pontos.
- **Integração de APIs Externas:** Estudar e implementar APIs adicionais, se necessário (ex: API de localização de ecopontos, envio de e-mail de confirmação).
- **Dockerização:** Criar os arquivos Dockerfile e docker-compose.yml para orquestrar os contêineres da aplicação.

### Júlia — Frontend & Banco de Dados

- **Interface Web (Frontend):** Desenvolver a interface do usuário usando HTML, CSS e JavaScript puro (Vanilla JS ou algum framework leve), focando em responsividade.
- **Captura de Imagem:** Implementar a lógica em JavaScript (navigator.mediaDevices.getUserMedia) para acessar a webcam do usuário, tirar a foto e enviá-la para a API via requisição HTTP (Fetch/Axios).
- **Modelagem e Setup do Banco de Dados:** Estruturar as tabelas (Usuários, Biometria, Pontuação, Histórico de Descartes).
- **Gestão do SGBD:** Configurar e integrar o banco de dados escolhido (preferencialmente MySQL para rodar junto ao Docker).

---

## 6. Arquitetura Tecnológica Definida

| Camada | Tecnologia |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python (FastAPI, Flask ou Django) |
| Banco de Dados | MySQL (Recomendado para arquitetura multi-contêiner) ou SQLite |
| Visão Computacional | OpenCV / Bibliotecas Python de biometria |
| Deploy e Ambiente | Docker e Docker Compose |

---
