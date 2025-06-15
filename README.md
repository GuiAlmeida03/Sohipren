# 📊 Sohipren - Análise e Previsão de Faturamento

Este é um aplicativo web interativo construído com Streamlit para analisar dados de faturamento a partir de um arquivo Excel. A ferramenta permite visualizar tendências históricas, decompor a série temporal em seus componentes principais (tendência, sazonalidade) e gerar previsões de faturamento futuro utilizando os modelos estatísticos SARIMA e Prophet.

## ✨ Funcionalidades Principais

* **📤 Upload Interativo:** Carregue facilmente seus relatórios de faturamento em formato `.xlsx`.
* **📉 Análise Descritiva:** Decomposição da série temporal para visualizar tendência, sazonalidade e resíduos.
* **🔮 Modelagem Preditiva:** Utilize modelos robustos como **Prophet** e **Auto-SARIMA** para prever o faturamento futuro.
* **📈 Métricas de Desempenho:** Avalie a precisão do modelo com métricas como MAE, RMSE, R² e MAPE.
* **🧑‍🤝‍🧑 Análise de Grupos:** Identifique e visualize a tendência de faturamento dos principais produtos e clientes.
* **📦 Previsão Individual:** Gere previsões de faturamento específicas para os produtos mais importantes.
* **🎛️ Interface Customizável:** Ajuste parâmetros do modelo, como frequência de agregação e períodos de previsão, diretamente na interface.
* **📥 Exportação de Dados:** Baixe os dados tratados e as tabelas de previsão em formato CSV.

## ⚙️ Como Funciona

O fluxo de trabalho da aplicação é o seguinte:

1.  **Carregamento e Limpeza:** O usuário carrega um arquivo Excel. A aplicação, usando a biblioteca Pandas, lê os dados, converte as colunas de data e trata valores ausentes ou não numéricos.
2.  **Agregação:** Os dados detalhados (diários, por nota) são agregados em uma frequência definida pelo usuário (mensal, semanal ou diária).
3.  **Análise e Modelagem:** A classe `FaturamentoForecast` executa o pipeline principal:
    * Decompõe a série temporal para análise.
    * Divide os dados em conjuntos de treino e teste.
    * Treina o modelo escolhido (Prophet ou SARIMA) com os dados de treino.
    * Valida o modelo com os dados de teste e calcula as métricas de erro.
4.  **Geração de Previsões:** Após o treinamento, o modelo é usado para prever os períodos futuros definidos pelo usuário.
5.  **Visualização:** Todos os resultados, incluindo gráficos de validação, previsão futura e análises de grupos, são exibidos na interface do Streamlit.

## 📁 Estrutura do Projeto

* `streamlit_app.py`: Script principal que define a interface do usuário e o fluxo da aplicação web com Streamlit.
* `faturamento_forecast_class.py`: Contém a classe `FaturamentoForecast`, que encapsula toda a lógica de negócio (carregamento de dados, tratamento, modelagem e geração de gráficos).
* `requirements.txt`: Lista de todas as bibliotecas Python necessárias para o projeto.
* `README.md`: Este arquivo de documentação.

## 🚀 Como Executar Localmente

Siga os passos abaixo para configurar e executar o projeto em sua máquina.

### Pré-requisitos

* Python 3.9 ou superior
* pip (gerenciador de pacotes do Python)
* Git (opcional, para clonar o repositório)

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/GuiAlmeida03/Sohipren-.git](https://github.com/GuiAlmeida03/Sohipren-.git)
    ```

2.  **Navegue até a pasta do projeto:**
    ```bash
    cd Sohipren-
    ```

3.  **Crie um ambiente virtual (altamente recomendado):**
    ```bash
    python -m venv venv
    ```

4.  **Ative o ambiente virtual:**
    * **No Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    * **No macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

5.  **Instale as dependências listadas no `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```

### Executando a Aplicação

Com o ambiente virtual ativado e as dependências instaladas, execute o seguinte comando no terminal:

```bash
streamlit run streamlit_app.py
