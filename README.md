# Sohipren - Análise e Previsão de Faturamento

![Linguagem](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Framework](https://img.shields.io/badge/Flask-2.x-black.svg)
![Análise](https://img.shields.io/badge/Pandas-2.x-blue.svg)
![Previsão](https://img.shields.io/badge/Prophet-1.1-blue.svg)
![Gráficos](https://img.shields.io/badge/Plotly-5.x-purple.svg)
![Banco de Dados](https://img.shields.io/badge/SQLite-3-blue.svg)
![Segurança](https://img.shields.io/badge/Bleach-6.x-orange.svg)

## 📖 Visão Geral

**Sohipren** é uma aplicação web completa, desenvolvida em Python com o framework Flask, projetada para realizar análises detalhadas e previsões de séries temporais de dados de faturamento. O projeto evoluiu de uma ferramenta de prototipagem para uma aplicação web robusta, multilíngue, segura e interativa, com persistência de dados.

A ferramenta permite que um usuário autenticado carregue um relatório de vendas em formato Excel, visualize KPIs (Key Performance Indicators) importantes, analise tendências, gere previsões de faturamento futuras usando o modelo **Prophet** e salve o histórico de todas as análises para consulta e reutilização futura.

## ✨ Principais Funcionalidades

- **Sistema de Autenticação:** Área administrativa protegida por login e senha, com controle de sessão e timeout por inatividade para maior segurança.
- **Segurança Reforçada:** Proteção contra ataques de Cross-Site Scripting (XSS) através da sanitização de todas as entradas do usuário com a biblioteca **Bleach**.
- **Upload de Dados Simplificado:** Carregue facilmente arquivos `.xlsx` através de uma interface web amigável.
- **Dashboard de KPIs:** Visualize instantaneamente os números mais importantes do seu negócio, como Faturamento Total, Ticket Médio, Total de Transações, Clientes e Produtos Únicos.
- **Previsão de Faturamento Configurável:** Utilize o poder do Prophet para gerar previsões, com parâmetros de modelo (frequência, períodos, sazonalidade, etc.) totalmente configuráveis pelo usuário.
- **Histórico Persistente:** Através da persistência de dados em um banco SQLite, todo o histórico de previsões e comparativos de produtos fica salvo. Isso permite que o usuário visualize, delete ou refaça análises antigas a qualquer momento.
- **Comparação de Produtos Dinâmica:** Selecione dois produtos para visualizar suas previsões de faturamento lado a lado. Para enriquecer a comparação, a aplicação realiza uma requisição externa através de web scraping no Google Imagens, buscando e exibindo dinamicamente as imagens correspondentes a cada peça.
- **Gráficos Interativos:** Todos os gráficos de previsão são gerados com a biblioteca **Plotly**, permitindo zoom, visualização de valores ao passar o mouse e a capacidade de ligar/desligar séries de dados clicando na legenda.
- **Exportação de Dados:** Exporte a tabela detalhada da previsão gerada para os formatos **CSV** e **Excel (.xlsx)** com um único clique.
- **Suporte a Múltiplos Idiomas (i18n):** A interface está totalmente traduzida para **Português, Inglês e Espanhol**, com um seletor manual para fácil alternância.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, Flask
- **Análise de Dados e Modelagem:** Pandas, Prophet (do Facebook)
- **Banco de Dados:** SQLite (nativo do Python)
- **Frontend:** HTML5, CSS3, Bootstrap 5 (via tema Bootswatch "Darkly")
- **Gráficos Interativos:** Plotly.js
- **Internacionalização (i18n):** Flask-Babel, Gettext
- **Segurança:** Bleach
- **Requisições Web:** Requests, BeautifulSoup4 (para busca de imagens)

## 📁 Estrutura do Projeto

```
.
|-- rep/
|   -- Sohipren-main/ | |-- __pycache__/ | |-- static/ | | |-- css/ | | |-- img/ | |-- plots/
|       |-- templates/
|       |-- tests/
|       |   |-- pycache/
|       |   |-- init.py
|       |   |-- conftest.py
|       |   -- test_app.py | |-- translations/ | | |-- en/LC_MESSAGES/ | | |-- es/LC_MESSAGES/ | |-- pt/LC_MESSAGES/
|       |-- uploads/
|       |-- app.py
|       |-- babel.cfg
|       |-- database.py
|       |-- desktop.ini
|       |-- faturamento_forecast_class.py
|       |-- historico.db
|       -- messages.pot |-- uploads/ |-- historico.db |-- requirements.txt-- 
```

## 🚀 Configuração e Instalação

Siga os passos abaixo para rodar o projeto em sua máquina local.

### Pré-requisitos
- [Git](https://git-scm.com/downloads)
- [Python](https://www.python.org/downloads/) (versão 3.10 ou superior)

### Passos de Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
    cd SEU_REPOSITORIO
    ```

2.  **Crie e ative um ambiente virtual (altamente recomendado):**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows (PowerShell)
    .\venv\Scripts\Activate.ps1

    # Ativar no Linux/macOS
    source venv/bin/activate
    ```

3.  **Instale todas as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## 🌐 Fluxo de Trabalho para Traduções (i18n)

A aplicação já vem com as traduções para Inglês e Espanhol. Caso você altere ou adicione textos na interface, siga os passos abaixo para atualizar os arquivos de tradução.

1.  **Extrair os textos:**
    ```bash
    pybabel extract -F babel.cfg -o messages.pot .
    ```

2.  **Atualizar os arquivos de idioma:**
    ```bash
    pybabel update -i messages.pot -d translations
    ```

3.  **Traduzir:** Abra os arquivos `.po` na pasta `translations` e preencha as novas traduções no campo `msgstr ""`.

4.  **Compilar as traduções:**
    ```bash
    pybabel compile -d translations
    ```

## ▶️ Como Executar a Aplicação

Com as dependências instaladas e as traduções compiladas, inicie o servidor Flask:

```bash
flask run --debug

O servidor estará rodando em modo de depuração. Abra seu navegador e acesse: http://127.0.0.1:5000

💡 Como Usar
1-Faça Login: Acesse a aplicação e entre com as credenciais de administrador (usuário: admin, senha: 123).
2-Navegue pelo Histórico: Na página inicial, visualize as análises de previsão e comparações realizadas anteriormente. Você pode deletá-las ou refazê-las com um clique.
3-Inicie uma Nova Análise: Vá para a página de análise para carregar um novo arquivo Excel.
4-Configure a Análise: Verifique se os nomes das colunas de Data, Valor, Produto e Cliente correspondem aos do seu arquivo. Ajuste os parâmetros do modelo conforme sua necessidade.
5-Execute: Clique em "Executar Análise".
6-Analise os Resultados: Navegue pelos KPIs, gráficos interativos e tabelas na página de resultados. Use a funcionalidade de comparação e exporte os dados se necessário.

```

## 📜 Histórico de Commits Pertinentes

```

f43e697  |  2025-06-15  |  Initial commit
1bfb013  |  2025-06-15  |  Meu primeiro commit com o projeto 
243cc05  |  2025-06-15  |  Merge branch 'main' of https://github.com/GuiAlmeida03/Sohipren-
845e4fd  |  2025-06-15  |  Update README.md
8cf8942  |  2025-06-16  |  Substitui versão Streamlit pelo projeto Flask completo
9aea260  |  2025-06-16  |  Update README.md
c11fb52  |  2025-06-16  |  Remove arquivo obsoleto streamlit_app.py
58e6877  |  2025-06-18  |  Removidos todos os arquivos do projeto
271e7bc  |  2025-06-18  |  Commit final do projeto Sohipren
2e7c766  |  2025-06-18  |  Create README.md 2

```





