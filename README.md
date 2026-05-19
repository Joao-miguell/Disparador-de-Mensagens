# 📲 Disparador de Mensagens

> Robô desktop para envio automatizado de mensagens via **WhatsApp Web**, desenvolvido com Python e Tkinter para a **Agência Maringá de Tecnologia e Inovação (AMTECH)**.

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Arquivos Gerados](#-arquivos-gerados)
- [Formato da Planilha](#-formato-da-planilha)
- [Variáveis da Mensagem](#-variáveis-da-mensagem)
- [Tecnologias](#-tecnologias)
- [Autores](#-autores)

---

## 💡 Sobre o Projeto

O **Disparador de Mensagens** é uma aplicação desktop que automatiza o envio de mensagens personalizadas pelo WhatsApp Web. Ele foi criado para facilitar a divulgação de cursos gratuitos de tecnologia oferecidos pela AMTECH em parceria com instituições como SENAI e SENAC.

A partir de uma planilha de alunos (`.xlsx`), o robô filtra os contatos de interesse, personaliza a mensagem com os dados do curso e envia automaticamente pelo WhatsApp Web — tudo com uma interface gráfica intuitiva e sem precisar de nenhuma API paga.

---

## ✨ Funcionalidades

- 📤 **Envio automatizado** de mensagens personalizadas via WhatsApp Web
- 🖼️ **Suporte a imagens** — envia uma imagem junto com o texto
- 🎯 **Filtragem por curso ou categoria** — envie só para quem se interessou pelo curso certo
- 📝 **Editor de mensagem embutido** com biblioteca de modelos salvos
- ⚙️ **Gerenciador de cursos embutido** — adicione, edite e remova categorias e cursos
- 👁️ **Preview da mensagem** — visualize o texto formatado antes de enviar
- ✅ **Validação automática da planilha** — verifica colunas e exibe contagem de contatos ao selecionar
- 🚫 **Histórico de envios** — evita duplicatas automaticamente
- 📊 **Barra de progresso** com status em tempo real (linha atual, total e número)
- 🎨 **18 temas visuais** configuráveis (claro, escuro, colorido)
- 💾 **Persistência total** — todas as configurações são salvas em arquivos locais

---

## 🗂️ Estrutura do Projeto

```
Disparador de Mensagens/
│
├── main.py                         # Ponto de entrada da aplicação
│
├── app/
│   ├── gui/
│   │   ├── main_window.py          # Janela principal com sistema de páginas embutidas
│   │   ├── message_editor.py       # Classe MessageEditor (reserva — UI embutida em main_window)
│   │   └── course_editor.py        # Classe CourseEditor (reserva — UI embutida em main_window)
│   │
│   ├── core/
│   │   ├── models.py               # Dataclass SendConfig (parâmetros de envio)
│   │   └── sender.py               # Lógica de envio (MessageSender)
│   │
│   └── utils/
│       ├── file_manager.py         # Leitura e escrita de todos os arquivos locais
│       └── widgets.py              # Componentes reutilizáveis (ToolTip, placeholder, scroll)
│
└── README.md
```

---

## ✅ Pré-requisitos

- **Python 3.11+**
- **Google Chrome** instalado (usado pelo WhatsApp Web)
- **WhatsApp Web** já logado no Chrome antes de iniciar o envio
- Sistema operacional: **Windows** (o envio de imagens usa PowerShell)

---

## 🚀 Instalação

**1. Clone o repositório**
```bash
git clone https://github.com/Joao-miguell/Disparador-de-Mensagens.git
cd Disparador-de-Mensagens
```

**2. Crie e ative um ambiente virtual (recomendado)**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

Caso não exista um `requirements.txt`, instale manualmente:
```bash
pip install ttkbootstrap pandas openpyxl pyautogui
```

**4. Execute a aplicação**
```bash
python main.py
```

---

## 🖥️ Como Usar

### 1. Preparar o ambiente
- Abra o **WhatsApp Web** no Chrome e faça login antes de iniciar qualquer envio.
- Deixe o Chrome aberto e visível durante todo o processo — o robô controla o navegador automaticamente.

### 2. Selecionar a planilha
Clique em **📁 Selecionar Planilha de Alunos** e escolha o arquivo `.xlsx` com os dados dos alunos. A aplicação valida automaticamente se as colunas obrigatórias existem e exibe o total de contatos encontrados. Veja o [formato esperado](#-formato-da-planilha) abaixo.

### 3. Escolher o modo de envio

| Modo | Descrição |
|---|---|
| **Normal** | Envia mensagem personalizada com variáveis do curso (nome, parceiro, horário etc.) |
| **Simples** | Envia a mensagem como está, sem substituir variáveis — útil para avisos genéricos |

> ⚠️ **Modo simples:** se a mensagem contiver `{chaves}`, elas aparecerão literalmente no texto enviado.

### 4. Configurar o curso (modo normal)
- Selecione o **curso** e a **instituição parceira** (SENAI ou SENAC)
- Preencha o **horário**, **data de início/fim** e **idade mínima**
- Escolha se quer enviar **por grupo** (toda a categoria) ou **somente pelo curso exato**

### 5. Definir o intervalo de linhas
- Informe a linha inicial e a linha final da planilha a processar
- O campo "Da linha" já sugere automaticamente a última linha processada

### 6. (Opcional) Pré-visualizar a mensagem
Clique em **👁️ Preview** para ver como a mensagem ficará formatada com os valores preenchidos, antes de disparar o envio.

### 7. Enviar
Clique em **🚀 ENVIAR MENSAGENS**. O robô abrirá cada contato no WhatsApp Web, enviará a mensagem e fechará a aba automaticamente.

> ⚠️ **Não mexa no mouse ou teclado durante o envio.** O robô usa automação de interface e qualquer interrupção pode causar erros.

### Editar mensagem e gerenciar cursos
Use os botões **📝 Editar Mensagem** e **⚙️ Gerenciar Cursos** no topo da tela. Eles abrem páginas embutidas dentro da própria janela — sem popups separados. Um botão **← Voltar** retorna à tela principal.

---

## 📁 Arquivos Gerados

Ao executar a aplicação, os seguintes arquivos são criados automaticamente na pasta raiz:

| Arquivo | Conteúdo |
|---|---|
| `config_cursos.json` | Categorias e cursos cadastrados |
| `templates_mensagens.json` | Biblioteca de modelos de mensagem |
| `mensagem_padrao.txt` | Mensagem atualmente ativa no robô |
| `last_line.json` | Última linha processada na planilha |
| `numeros_enviados.json` | Histórico de números que já receberam mensagem |
| `settings.json` | Tema visual selecionado |
| `mensagens_enviadas.log` | Log de todos os envios realizados |

---

## 📊 Formato da Planilha

O arquivo `.xlsx` deve conter **exatamente** as seguintes colunas (os nomes devem ser idênticos, sem espaços extras):

| Coluna | Obrigatória | Descrição |
|---|---|---|
| `Nome Completo` | ✅ Sempre | Nome do aluno para personalizar a mensagem |
| `Whatsapp com DDD (somente números - sem espaço)` | ✅ Sempre | Número de WhatsApp com DDD |
| `Dentre as opções qual curso gostaria de fazer?` | ✅ Modo normal | Cursos de interesse, separados por vírgula e espaço |

**Exemplo de linha válida:**

| Nome Completo | Whatsapp com DDD... | Dentre as opções... |
|---|---|---|
| João Silva | 44999998888 | Programação Web, Excel Avançado |

---

## 🔤 Variáveis da Mensagem

No editor de mensagem, use as variáveis abaixo entre `{ }` — o robô as substituirá automaticamente pelos valores preenchidos na interface:

| Variável | Substituído por |
|---|---|
| `{nome}` | Nome do aluno na planilha |
| `{parceiro}` | Instituição selecionada (SENAI / SENAC) |
| `{curso}` | Nome do curso selecionado |
| `{idade_minima}` | Idade mínima preenchida |
| `{duracao}` | Data de início e fim do curso |
| `{horario}` | Horário do curso |

---

## 🛠️ Tecnologias

| Tecnologia | Uso |
|---|---|
| [Python 3.11+](https://www.python.org/) | Linguagem principal |
| [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) | Interface gráfica moderna |
| [pandas](https://pandas.pydata.org/) | Leitura e processamento da planilha |
| [openpyxl](https://openpyxl.readthedocs.io/) | Suporte a arquivos `.xlsx` |
| [pyautogui](https://pyautogui.readthedocs.io/) | Automação de teclado e mouse |
| [webbrowser](https://docs.python.org/3/library/webbrowser.html) | Abertura do WhatsApp Web |
| [threading](https://docs.python.org/3/library/threading.html) | Envio em background sem travar a UI |

---

## 👨‍💻 Autores

Desenvolvido por:

- **Lucas Ferrari**
- **Eduardo Zanin**
- **João Miguel**

Projeto desenvolvido para a **AMTECH — Agência Maringá de Tecnologia e Inovação**.
