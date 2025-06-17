# Sohipren - Análise e Previsão de Faturamento

![Linguagem](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Framework](https://img.shields.io/badge/Flask-2.x-black.svg)
![Análise](https://img.shields.io/badge/Pandas-2.x-blue.svg)
![Previsão](https://img.shields.io/badge/Prophet-1.1-blue.svg)
![Gráficos](https://img.shields.io/badge/Plotly-5.x-purple.svg)
![Tradução](https://img.shields.io/badge/Babel-2.x-red.svg)

## 📖 Visão Geral

**Sohipren** é uma aplicação web completa, desenvolvida em Python com o framework Flask, projetada para realizar análises detalhadas e previsões de séries temporais de dados de faturamento. O projeto evoluiu de uma ferramenta de prototipagem para uma aplicação web robusta, multilíngue e interativa.

A ferramenta permite que um usuário carregue um relatório de vendas em formato Excel, visualize KPIs (Key Performance Indicators) importantes, analise tendências e gere previsões de faturamento futuras usando o modelo **Prophet** do Facebook.

## ✨ Principais Funcionalidades

- **Upload de Dados Simplificado:** Carregue facilmente arquivos `.xlsx` através de uma interface web amigável.
- **Dashboard de KPIs:** Visualize instantaneamente os números mais importantes do seu negócio, como Faturamento Total, Ticket Médio, Total de Transações, Clientes e Produtos Únicos.
- **Previsão de Faturamento Configurável:** Utilize o poder do Prophet para gerar previsões, com parâmetros de modelo (frequência, períodos, sazonalidade, etc.) totalmente configuráveis pelo usuário.
- **Gráficos Interativos:** Todos os gráficos de previsão são gerados com a biblioteca **Plotly**, permitindo zoom, visualização de valores ao passar o mouse e a capacidade de ligar/desligar séries de dados clicando na legenda.
- **Comparação de Produtos:** Selecione dois produtos e visualize suas previsões de faturamento lado a lado em gráficos interativos para uma análise comparativa direta.
- **Exportação de Dados:** Exporte a tabela detalhada da previsão gerada para os formatos **CSV** e **Excel (.xlsx)** com um único clique.
- **Suporte a Múltiplos Idiomas (i18n):** A interface está totalmente traduzida para **Português, Inglês e Espanhol**, com um seletor manual para fácil alternância.

- ## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, Flask
- **Análise de Dados e Modelagem:** Pandas, Prophet (do Facebook)
- **Frontend:** HTML5, CSS3, Bootstrap 5 (via tema Bootswatch "Darkly")
- **Gráficos Interativos:** Plotly.js
- **Internacionalização (i18n):** Flask-Babel, Gettext

- ## 📁 Estrutura do Projeto

- sohipren-flask/
|-- app.py                # Servidor Flask, rotas e lógica principal da aplicação
|-- faturamento_forecast_class.py # Classe com toda a lógica de análise e previsão
|-- static/               # Arquivos estáticos (CSS, JS, Imagens)
|   -- css/ |-- style.css     # Estilos customizados (ex: inputs escuros)
|-- templates/            # Templates HTML (a "cara" do site)
|   |-- index.html        # Página inicial com o formulário de upload e configuração
|   -- results.html # Página que exibe todos os resultados da análise |-- translations/ # Pasta com os arquivos de tradução | |-- en/LC_MESSAGES/ | | |-- messages.po # Arquivo de tradução para Inglês | |-- messages.mo   # Arquivo compilado de tradução
|   -- es/LC_MESSAGES/ | |-- messages.po # Arquivo de tradução para Espanhol |-- messages.mo   # Arquivo compilado de tradução
|-- uploads/              # Pasta temporária para arquivos carregados e gerados
|-- .gitignore            # Arquivos e pastas a serem ignorados pelo Git
|-- babel.cfg             # Arquivo de configuração para o Flask-Babel
`-- requirements.txt      # Lista de todas as dependências do projeto

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

1.  **Extrair os textos:** Este comando varre o código em busca de textos novos e atualiza o arquivo "molde" `messages.pot`.
    ```bash
    python -m babel.messages.frontend extract -F babel.cfg -o messages.pot .
    ```

2.  **Atualizar os arquivos de idioma:** Este comando mescla as novas alterações nos arquivos `.po` de cada idioma.
    ```bash
    python -m babel.messages.frontend update -i messages.pot -d translations
    ```

3.  **Traduzir:** Abra os arquivos `.po` na pasta `translations` e preencha as novas traduções no campo `msgstr ""`.

4.  **Compilar as traduções:** Este é o passo final para que as traduções apareçam na aplicação.
    ```bash
    python -m babel.messages.frontend compile -d translations
    ```

    ## ▶️ Como Executar a Aplicação

Com as dependências instaladas e as traduções compiladas, inicie o servidor Flask com o seguinte comando:

```bash
python -m flask run --debug

O servidor estará rodando em modo de depuração. Abra seu navegador e acesse:

https://www.google.com/search?q=http://127.0.0.1:5000



## 💡 Como Usar

1.  **Escolha o Idioma:** Utilize os links no canto superior direito para alternar entre Português, Inglês e Espanhol.
2.  **Carregue o Arquivo:** Na página inicial, clique para carregar seu arquivo Excel.
3.  **Configure a Análise:** Verifique se os nomes das colunas de Data, Valor, Produto e Cliente correspondem aos do seu arquivo. Ajuste os parâmetros do modelo conforme sua necessidade.
4.  **Execute:** Clique em "Executar Análise".
5.  **Analise os Resultados:** Navegue pelos KPIs, gráficos interativos e tabelas na página de resultados. Use a funcionalidade de comparação e exporte os dados se necessário.
