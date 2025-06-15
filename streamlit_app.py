# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import os
import traceback # Importado globalmente

# Import the modified class from the separate file
from faturamento_forecast_class import FaturamentoForecast

# --- Page Configuration ---
st.set_page_config(
    page_title="Previsão de Faturamento",
    page_icon="📊",
    layout="wide"
)

# --- Initialize Session State ---
# Estas são as variáveis que precisam persistir entre as re-execuções do script
if 'file_bytes_io' not in st.session_state:
    st.session_state.file_bytes_io = None
if 'current_uploaded_filename' not in st.session_state:
    st.session_state.current_uploaded_filename = None
if 'forecast_instance' not in st.session_state:
    st.session_state.forecast_instance = None # Armazenará a instância da sua classe
if 'pipeline_results' not in st.session_state:
    st.session_state.pipeline_results = None # Armazenará o dicionário de resultados do pipeline
if 'main_analysis_triggered' not in st.session_state:
    # Flag para saber se o botão principal foi clicado e a análise deve prosseguir
    st.session_state.main_analysis_triggered = False
if 'individual_product_selected' not in st.session_state:
    st.session_state.individual_product_selected = None
if 'individual_model_selected' not in st.session_state:
    st.session_state.individual_model_selected = 'Prophet' # Default AGORA É O ÚNICO
if 'individual_forecast_fig' not in st.session_state:
    st.session_state.individual_forecast_fig = None


# --- Helper Functions (Mantendo as suas, com pequenos ajustes se necessário) ---
@st.cache_data # Cache the raw data loading based on file content
def load_raw_data_bytes(uploaded_file_content, filename):
    """Loads data from uploaded file content (bytes) into BytesIO."""
    if uploaded_file_content is not None:
        try:
            return io.BytesIO(uploaded_file_content)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo Excel: {e}")
            return None
    return None

# Não vamos cachear a instância inteira, mas sim os resultados de suas operações quando possível.
# A instância em si será gerenciada pelo session_state.
def run_analysis_pipeline_local(_forecast_instance, **params):
    """Runs the full pipeline and returns the results dictionary."""
    try:
        results = _forecast_instance.executar_pipeline_completo(**params)
        return results
    except Exception as e:
        st.error(f"Erro durante a execução do pipeline: {e}")
        st.error(f"Detalhes do erro:\n{traceback.format_exc()}")
        return None

# O cache para a previsão individual é útil, pois os parâmetros podem se repetir.
@st.cache_resource(ttl=3600)
def run_individual_product_forecast_cached(instance_file_id, product_name, product_col, freq, periods, model):
    """
    Runs and caches individual product forecast.
    `instance_file_id` é um identificador para ajudar o cache (ex: nome do arquivo).
    A instância real será pega do session_state.
    """
    if 'forecast_instance' not in st.session_state or st.session_state.forecast_instance is None:
        st.warning("Instância de forecast não está pronta para previsão individual.")
        return None
    _forecast_instance = st.session_state.forecast_instance
    try:
        if hasattr(_forecast_instance, 'prever_produto_individual'):
            fig = _forecast_instance.prever_produto_individual(
                nome_produto=product_name,
                coluna_produto=product_col,
                freq=freq,
                periodos=periods,
                model_type=model
            )
            return fig
        else:
            st.error("Funcionalidade 'prever_produto_individual' não encontrada na classe de forecast.")
            return None
    except Exception as e:
        st.error(f"Erro ao gerar previsão para {product_name}: {e}")
        st.error(f"Detalhes do erro:\n{traceback.format_exc()}")
        return None

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- Main App ---
st.title("📊 Análise e Previsão de Faturamento")
st.markdown(
    "Bem-vindo! Esta ferramenta ajuda você a entender o comportamento passado do seu faturamento "
    "e a prever como ele poderá ser no futuro. Basta carregar seu relatório de vendas em Excel."
)
st.markdown("---")

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("⚙️ Controles da Análise")

    uploaded_file = st.file_uploader("1. Carregar Arquivo Excel (.xlsx)", type="xlsx",
                                     help="Selecione o arquivo Excel contendo os dados de faturamento detalhado.")

    # Lógica de carregamento e reset de estado
    if uploaded_file is not None:
        if st.session_state.current_uploaded_filename != uploaded_file.name:
            st.toast(f"Processando novo arquivo: {uploaded_file.name}")
            file_content_bytes = uploaded_file.getvalue()
            st.session_state.file_bytes_io = load_raw_data_bytes(file_content_bytes, uploaded_file.name)
            st.session_state.current_uploaded_filename = uploaded_file.name
            # Resetar estados dependentes do arquivo para forçar re-análise
            st.session_state.forecast_instance = None
            st.session_state.pipeline_results = None
            st.session_state.main_analysis_triggered = False # Importante
            st.session_state.individual_forecast_fig = None
            if st.session_state.file_bytes_io:
                st.success(f"Arquivo '{uploaded_file.name}' pronto.")
            else:
                st.error("Falha ao carregar o arquivo.")
    elif st.session_state.current_uploaded_filename is not None: # Se não há arquivo carregado mas havia um antes
        # Manter o último arquivo processado se o usuário remover o upload atual
        pass


    st.markdown("---")
    st.subheader("ℹ️ Como Usar")
    st.caption(
        "1. **Carregue seu arquivo Excel**.\n"
        "2. **Verifique os Nomes das Colunas**.\n"
        "3. **Escolha o Modelo Principal** e ajuste as configurações.\n"
        "4. **Defina Opções de Análise Adicional**.\n"
        "5. **Clique em '🚀 Executar Análise'**."
    )
    st.markdown("---")

    st.subheader("Nomes das Colunas no seu Arquivo")
    # Usar st.session_state para manter os valores dos inputs entre re-execuções
    col_data = st.text_input("Coluna de Data", st.session_state.get('col_data_val', "EMISSÃO"))
    col_valor = st.text_input("Coluna de Valor", st.session_state.get('col_valor_val', "VALOR TOTAL"))
    col_prod = st.text_input("Coluna de Produto (Opcional)", st.session_state.get('col_prod_val', "DESCRIÇÃO MATERIAL"))
    col_cli = st.text_input("Coluna de Cliente (Opcional)", st.session_state.get('col_cli_val', "RAZÃO SOCIAL CLIENTE"))

    # Atualizar o session_state com os valores atuais dos inputs
    st.session_state.col_data_val = col_data
    st.session_state.col_valor_val = col_valor
    st.session_state.col_prod_val = col_prod
    st.session_state.col_cli_val = col_cli


    st.markdown("---")
    st.subheader("Configurações do Modelo de Previsão")
    model_choice = st.selectbox("Escolha o Modelo Principal", ["Prophet", "SARIMA"], index=st.session_state.get('model_choice_idx', 0), key="model_choice_sb")
    st.session_state.model_choice_idx = ["Prophet", "SARIMA"].index(model_choice)

    freq_agg_map = {'Mensal': 'M', 'Semanal': 'W', 'Diário': 'D'}
    freq_agg_display_options = list(freq_agg_map.keys())
    freq_agg_display = st.selectbox("Frequência de Agregação dos Dados", freq_agg_display_options, index=st.session_state.get('freq_agg_idx',0), key="freq_agg_sb")
    st.session_state.freq_agg_idx = freq_agg_display_options.index(freq_agg_display)
    freq_agg = freq_agg_map[freq_agg_display]

    periodo_sazonal = st.number_input("Período Sazonal Principal", min_value=1, value=st.session_state.get('periodo_sazonal_val', 12), step=1, key="periodo_sazonal_ni")
    st.session_state.periodo_sazonal_val = periodo_sazonal

    test_ratio_val = st.slider("Proporção de Dados para Teste (%)", min_value=10, max_value=50, value=st.session_state.get('test_ratio_slider_val', 20), step=5, key="test_ratio_sl") / 100.0
    st.session_state.test_ratio_slider_val = int(test_ratio_val * 100) # Salva o valor do slider
    test_ratio = test_ratio_val

    periodos_forecast_val = st.number_input("Períodos para Prever no Futuro", min_value=1, value=st.session_state.get('periodos_forecast_val', 12), step=1, key="periodos_forecast_ni")
    st.session_state.periodos_forecast_val = periodos_forecast_val
    periodos_forecast = periodos_forecast_val


    with st.expander(f"Parâmetros Avançados do Modelo: {model_choice}", expanded=False):
        if model_choice == "Prophet":
            prophet_seasonality_mode_options = ['additive', 'multiplicative']
            prophet_seasonality_mode = st.selectbox("Modo da Sazonalidade (Prophet)", prophet_seasonality_mode_options, index=st.session_state.get('prophet_mode_idx',1), key="prophet_mode_sb")
            st.session_state.prophet_mode_idx = prophet_seasonality_mode_options.index(prophet_seasonality_mode)

            prophet_changepoint_prior_scale_val = st.slider("Flexibilidade da Tendência (Prophet)", 0.01, 1.0, st.session_state.get('prophet_cp_scale',0.65), 0.01, key="prophet_cp_sl")
            st.session_state.prophet_cp_scale = prophet_changepoint_prior_scale_val
            prophet_changepoint_prior_scale = prophet_changepoint_prior_scale_val

            prophet_seasonality_prior_scale_val = st.slider("Força da Sazonalidade (Prophet)", 1.0, 50.0, st.session_state.get('prophet_seas_scale',25.0), 1.0, key="prophet_seas_sl")
            st.session_state.prophet_seas_scale = prophet_seasonality_prior_scale_val
            prophet_seasonality_prior_scale = prophet_seasonality_prior_scale_val
        else: # SARIMA
            sarima_stepwise_val = st.checkbox("Busca Stepwise (SARIMA - mais rápida)", value=st.session_state.get('sarima_stepwise_val', True), key="sarima_stepwise_cb")
            st.session_state.sarima_stepwise_val = sarima_stepwise_val
            sarima_stepwise = sarima_stepwise_val
            st.caption("As ordens (p,d,q)(P,D,Q,m) do SARIMA serão detectadas automaticamente (auto_arima).")

    st.markdown("---")
    st.subheader("Análises Descritivas Adicionais")
    analisar_produtos_val = st.checkbox("Analisar Top Produtos", value=st.session_state.get('analisar_prod_val', True), key="analisar_prod_cb")
    st.session_state.analisar_prod_val = analisar_produtos_val
    analisar_produtos = analisar_produtos_val

    top_produtos_val = st.number_input("Número de Top Produtos para Análise", min_value=3, max_value=20, value=st.session_state.get('top_prod_val', 10), step=1, disabled=not analisar_produtos, key="top_prod_ni")
    st.session_state.top_prod_val = top_produtos_val
    top_produtos = top_produtos_val

    analisar_clientes_val = st.checkbox("Analisar Top Clientes", value=st.session_state.get('analisar_cli_val', True), key="analisar_cli_cb")
    st.session_state.analisar_cli_val = analisar_clientes_val
    analisar_clientes = analisar_clientes_val

    top_clientes_val = st.number_input("Número de Top Clientes para Análise", min_value=3, max_value=20, value=st.session_state.get('top_cli_val', 10), step=1, disabled=not analisar_clientes, key="top_cli_ni")
    st.session_state.top_cli_val = top_clientes_val
    top_clientes = top_clientes_val

    st.markdown("---")
    if st.button("🚀 Executar Análise e Previsão", disabled=(st.session_state.file_bytes_io is None), use_container_width=True, key="run_main_analysis_btn"):
        st.session_state.main_analysis_triggered = True # Sinaliza que o botão foi clicado
        # Resetar figura individual anterior quando a análise principal é re-executada
        st.session_state.individual_forecast_fig = None
        # Forçar a re-execução a partir daqui para que as próximas seções usem o novo estado
        st.rerun()


# --- Lógica Principal de Execução e Exibição de Resultados ---

if st.session_state.get('main_analysis_triggered', False) and st.session_state.file_bytes_io is not None:
    # Só executa o pipeline se ainda não tiver resultados ou se a instância não existir
    if st.session_state.forecast_instance is None or st.session_state.pipeline_results is None:
        with st.spinner("☕ Preparando a análise e instanciando o motor de previsão..."):
            st.session_state.forecast_instance = FaturamentoForecast(
                file_input=st.session_state.file_bytes_io, 
                coluna_data=col_data,
                coluna_valor=col_valor
            )

        pipeline_params = {
            'modelo_tipo': model_choice.lower(), 'freq_agg': freq_agg, 'periodo_sazonal': periodo_sazonal,
            'tratar_outliers_antes_agg': False, 'test_ratio': test_ratio, 'periodos_forecast': periodos_forecast,
            'analisar_produtos': analisar_produtos, 'coluna_produto': col_prod, 'top_produtos': top_produtos,
            'analisar_clientes': analisar_clientes, 'coluna_cliente': col_cli, 'top_clientes': top_clientes
        }
        if model_choice == "Prophet":
            pipeline_params.update({
                'prophet_seasonality_mode': prophet_seasonality_mode,
                'prophet_changepoint_prior_scale': prophet_changepoint_prior_scale,
                'prophet_seasonality_prior_scale': prophet_seasonality_prior_scale,
            })
        else: # SARIMA
            pipeline_params.update({'sarima_stepwise': sarima_stepwise})

        with st.spinner(f"⚙️ Executando o pipeline de análise com o modelo {model_choice}... Isso pode levar alguns minutos."):
            st.session_state.pipeline_results = run_analysis_pipeline_local(st.session_state.forecast_instance, **pipeline_params)

        if st.session_state.pipeline_results and st.session_state.forecast_instance.df_raw is not None:
            st.success("🎉 Análise principal concluída com sucesso!")
        else:
            st.session_state.pipeline_results = None 
            st.error(
                "❌ Falha ao executar o pipeline de análise. "
                "Verifique as configurações e tente novamente. "
                "Verifique o console para detalhes técnicos do erro."
            )
            st.session_state.main_analysis_triggered = False


# Exibir resultados SE existirem no session_state
if st.session_state.get('pipeline_results') is not None:
    results = st.session_state.pipeline_results
    forecast_instance_ref = st.session_state.forecast_instance 

    st.markdown("---")
    st.header("📈 Resultados da Previsão Geral do Faturamento")
    if results['metricas'] or results['metricas_avancadas']:
        st.subheader("Métricas de Avaliação do Modelo (no período de teste)")
        st.markdown(
            "Estas métricas indicam o quão bem o modelo performou ao prever dados do passado que ele não viu durante o treinamento. "
            "Valores menores para MAE, RMSE, MAPE e SMAPE geralmente indicam um modelo mais preciso."
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("MAE (Erro Médio Absoluto)", f"{results['metricas'].get('MAE', 0):,.0f}")
            st.caption(f"Em média, a previsão errou em R$ {results['metricas'].get('MAE', 0):,.0f} o valor real no período de teste.")
        with col2:
            st.metric("RMSE (Raiz do Erro Quadrático Médio)", f"{results['metricas'].get('RMSE', 0):,.0f}")
            st.caption("Similar ao MAE, mas penaliza mais os erros grandes.")
        with col3:
            st.metric("R² (Coeficiente de Determinação)", f"{results['metricas'].get('R²', 0):.3f}")
            st.caption("Indica o quão bem o modelo se ajusta aos dados (entre 0 e 1). Mais próximo de 1 é geralmente melhor, mas não é a única medida de um bom modelo.")

        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("MAPE (Erro Percentual Médio Absoluto)", f"{results['metricas_avancadas'].get('MAPE (%)', 0):.2f}%")
            st.caption(f"Em média, a previsão errou em {results['metricas_avancadas'].get('MAPE (%)', 0):.2f}% em relação ao valor real. Útil para comparar precisão entre séries de diferentes escalas.")
        with col5:
            st.metric("SMAPE (Erro Percentual Médio Absoluto Simétrico)", f"{results['metricas_avancadas'].get('SMAPE (%)', 0):.2f}%")
            st.caption("Similar ao MAPE, mas mais estável quando os valores reais são próximos de zero.")
        with col6:
            st.metric("Viés (MPE - Erro Percentual Médio)", f"{results['metricas_avancadas'].get('MPE (%) (Viés)', 0):.2f}%")
            st.caption("Indica se o modelo tende a superestimar (valor negativo) ou subestimar (valor positivo) as previsões.")
        st.divider()

    tab_forecast, tab_validation, tab_decomp, tab_diag = st.tabs([
        "🗓️ Previsão Futura", "⚖️ Validação do Modelo", "🔬 Decomposição da Série", "⚙️ Diagnóstico do Modelo"
    ])

    with tab_forecast:
        st.subheader("Previsão de Faturamento para os Próximos Períodos")
        if results['previsao_futura_fig']:
            st.pyplot(results['previsao_futura_fig'])
            st.markdown(
                f"""
                Este gráfico mostra:
                - Em **azul**: Seu faturamento histórico.
                - Em **laranja tracejado**: A previsão de faturamento para os próximos {periodos_forecast} {freq_agg_display.lower()}s.
                - A **área sombreada laranja**: O intervalo de confiança da previsão. Há uma probabilidade de 95% de que o valor real futuro esteja dentro desta faixa, assumindo que os padrões passados continuem.
                """
            )
        else:
            st.warning("Gráfico de previsão futura não pôde ser gerado.")

        if results['previsao_futura_df'] is not None:
            with st.expander("Ver Tabela Detalhada da Previsão Futura"):
                    st.dataframe(results['previsao_futura_df'].style.format("{:,.2f}"), use_container_width=True)
            csv_forecast = convert_df_to_csv(results['previsao_futura_df'].reset_index())
            st.download_button(
                label="📥 Baixar Tabela de Previsão Futura (CSV)",
                data=csv_forecast,
                file_name=f"previsao_faturamento_{model_choice.lower()}_{freq_agg_display.lower()}.csv",
                mime="text/csv",
            )

    with tab_validation:
        st.subheader("Validação do Modelo: Real vs. Previsto (no período de teste)")
        if results['validacao_fig']:
            st.pyplot(results['validacao_fig'])
            st.markdown(
                """
                Este gráfico compara:
                - Em **cinza**: Os dados históricos usados para treinar o modelo.
                - Em **verde**: Os valores reais do período de teste (dados que o modelo não viu durante o treino).
                - Em **laranja tracejado**: As previsões que o modelo fez para esse mesmo período de teste.
                Quanto mais próxima a linha laranja estiver da verde, melhor foi o desempenho do modelo em prever o passado recente.
                A área sombreada laranja é o intervalo de confiança para essas previsões de teste.
                """
            )
        else:
            st.warning("Gráfico de validação não pôde ser gerado.")

    with tab_decomp:
        st.subheader("Decomposição da Série Temporal do Faturamento")
        if results['decomposicao_fig']:
            st.pyplot(results['decomposicao_fig'])
            st.markdown(
                """
                Este gráfico separa seu faturamento agregado em diferentes componentes para melhor entendimento:
                - **Observado:** Seus dados de faturamento originais agregados.
                - **Tendência:** A direção geral do seu faturamento ao longo do tempo (está crescendo, diminuindo ou estável?).
                - **Sazonalidade:** Padrões que se repetem em intervalos regulares (ex: vendas mais altas em certos meses ou dias da semana).
                - **Resíduos:** As flutuações que não são explicadas pela tendência ou pela sazonalidade. Idealmente, são aleatórios e pequenos.
                """
            )
        else:
            st.warning("Gráfico de decomposição não pôde ser gerado.")

    with tab_diag:
            st.subheader(f"Diagnóstico Técnico do Modelo ({model_choice})")
            if model_choice == "SARIMA":
                diag_figs = results.get('diagnostico_figs', {})
                if diag_figs.get('diagnostics'):
                    st.pyplot(diag_figs['diagnostics'])
                    st.markdown(
                             """
                             **Diagnóstico de Resíduos do SARIMA:**
                             - **Resíduos ao Longo do Tempo (superior):** Idealmente, os resíduos (erros do modelo) devem flutuar aleatoriamente em torno de zero, sem padrões óbvios.
                             - **Histograma (inferior esquerdo):** Mostra a distribuição dos resíduos. Espera-se que se assemelhe a uma distribuição normal (curva sino).
                             - **Q-Q Plot (inferior direito):** Compara os resíduos com uma distribuição normal. Pontos próximos à linha vermelha indicam normalidade.
                             """
                         )
                else: st.write("Gráfico de Diagnóstico de Resíduos não gerado.")
                if diag_figs.get('acf'):
                    st.pyplot(diag_figs['acf'])
                    st.markdown(
                             """
                             **Autocorrelação dos Resíduos (ACF - SARIMA):**
                             Este gráfico mostra se os erros do modelo estão correlacionados entre si em diferentes defasagens (lags).
                             Idealmente, todas as barras devem estar dentro da área azul (intervalo de confiança), indicando que não há correlação significativa remanescente nos resíduos.
                             """
                         )
                else: st.write("Gráfico ACF dos Resíduos não gerado.")

            elif model_choice == "Prophet":
                diag_figs = results.get('diagnostico_figs', {})
                if diag_figs.get('componentes'):
                    st.pyplot(diag_figs['componentes'])
                    st.markdown(
                             """
                             **Componentes do Modelo Prophet:**
                             Este gráfico mostra como o Prophet enxerga e modela os diferentes aspectos dos seus dados:
                             - **trend:** A tendência geral de crescimento ou queda.
                             - **yearly/weekly/daily:** Os padrões sazonais anuais, semanais ou diários que o modelo detectou.
                             - **holidays (se aplicável):** O impacto de feriados ou eventos especiais, se configurados.
                             - **extra_regressors (se aplicável):** O impacto de outras variáveis que você possa ter adicionado ao modelo.
                             """
                         )
                else: st.write("Gráfico de Componentes Prophet não gerado.")
            else: st.write("Diagnóstico não aplicável ou não gerado para este modelo.")
    st.divider()

    st.header("📊 Análise Descritiva de Faturamento")
    tab_prod_desc, tab_cli_desc = st.tabs(["🛍️ Tendência por Produto", "👥 Tendência por Cliente"])

    with tab_prod_desc:
        if analisar_produtos: 
            st.subheader(f"Tendência de Faturamento dos Top {top_produtos} Produtos")
            if results['top_produtos_fig']:
                st.pyplot(results['top_produtos_fig'])
                st.markdown(
                    f"O gráfico acima mostra a evolução mensal do faturamento para os {top_produtos} produtos que mais contribuíram para a receita total "
                    "ao longo do período analisado. Isso pode ajudar a identificar produtos com crescimento consistente, sazonais ou em declínio."
                )
            else: st.warning("Gráfico de tendência de produtos não gerado. Verifique se a coluna de produto está correta e se há dados suficientes.")
            if not results['top_produtos_list']:
                    st.info(f"Não foram encontrados dados suficientes ou a coluna '{col_prod}' não permitiu a análise dos top produtos.")
        else: st.info("Análise de produtos desativada. Marque a opção na barra lateral para ativá-la.")

    with tab_cli_desc:
            if analisar_clientes: 
                st.subheader(f"Tendência de Faturamento dos Top {top_clientes} Clientes")
                if results['top_clientes_fig']:
                    st.pyplot(results['top_clientes_fig'])
                    st.markdown(
                        f"O gráfico acima mostra a evolução mensal do faturamento para os {top_clientes} clientes que mais geraram receita "
                        "ao longo do período analisado. Isso pode ajudar a identificar clientes chave, sua consistência de compra e potenciais riscos ou oportunidades."
                    )
                else: st.warning("Gráfico de tendência de clientes não gerado. Verifique se a coluna de cliente está correta e se há dados suficientes.")
                if not results['top_clientes_list']:
                    st.info(f"Não foram encontrados dados suficientes ou a coluna '{col_cli}' não permitiu a análise dos top clientes.")
            else: st.info("Análise de clientes desativada. Marque a opção na barra lateral para ativá-la.")
    st.divider()

    # Seção de Previsão Individual
    if analisar_produtos and results.get('top_produtos_list'):
            st.header("🔍 Previsão Individual por Produto")
            st.markdown("Selecione um produto da lista dos Top Produtos para ver uma previsão de faturamento individual para ele. "
                        "Isso pode ajudar a entender as perspectivas futuras de produtos específicos.")

            top_produto_options = results.get('top_produtos_list', [])

            if top_produto_options:
                st.session_state.individual_product_selected = st.selectbox(
                    "Selecione o Produto para Previsão Individual", options=top_produto_options,
                    index=top_produto_options.index(st.session_state.individual_product_selected) if st.session_state.individual_product_selected in top_produto_options else 0,
                    key="indiv_prod_sb_selector" 
                )
                
                # ETS Removido - Modelo fixo como Prophet
                st.session_state.individual_model_selected = 'Prophet'
                st.caption(f"Modelo para previsão individual: **{st.session_state.individual_model_selected}**")


                if st.button(f"Gerar Previsão para '{st.session_state.individual_product_selected}' (com {st.session_state.individual_model_selected})", key="run_indiv_btn_trigger"):
                    if st.session_state.forecast_instance:
                        with st.spinner(f"⏳ Gerando previsão para '{st.session_state.individual_product_selected}'..."):
                            filename_for_cache = st.session_state.current_uploaded_filename or "default_file"
                            fig = run_individual_product_forecast_cached(
                                instance_file_id=filename_for_cache,
                                product_name=st.session_state.individual_product_selected,
                                product_col=col_prod, 
                                freq=freq_agg, 
                                periods=periodos_forecast, 
                                model=st.session_state.individual_model_selected.lower() # Sempre 'prophet'
                            )
                            st.session_state.individual_forecast_fig = fig
                            st.rerun()
                    else:
                        st.warning("Instância de forecast não disponível. Execute a análise principal primeiro.")

                if st.session_state.get('individual_forecast_fig'):
                    st.pyplot(st.session_state.individual_forecast_fig)
                    st.markdown(f"Previsão de faturamento para o produto **{st.session_state.individual_product_selected}** usando o modelo {st.session_state.individual_model_selected}. "
                                "Interprete com cautela, pois modelos individuais podem ter precisão variável dependendo da quantidade e padrão dos dados do produto.")
                elif st.session_state.individual_forecast_fig is False: 
                    st.warning(f"Não foi possível gerar a previsão individual para '{st.session_state.individual_product_selected}'. Verifique se há dados suficientes para este produto e se não ocorreram erros (logs no console).")

            else: st.info("Lista de Top Produtos não disponível para seleção. Execute a análise de produtos primeiro.")
    elif analisar_produtos: 
        st.info("Execute a análise principal com 'Analisar Top Produtos' marcado para habilitar a previsão individual.")


    with st.expander("📥 Opções de Download de Dados Adicionais"):
        if forecast_instance_ref and forecast_instance_ref.df_raw is not None:
            st.download_button("Baixar Dados Brutos Tratados (CSV)", convert_df_to_csv(forecast_instance_ref.df_raw), "dados_brutos_tratados.csv", mime="text/csv")
        if forecast_instance_ref and forecast_instance_ref.df_agregado is not None:
            st.download_button(f"Baixar Dados Agregados por {freq_agg_display} (CSV)", convert_df_to_csv(forecast_instance_ref.df_agregado.reset_index()), f"dados_agregados_{freq_agg_display.lower()}.csv", mime="text/csv")


elif st.session_state.get('main_analysis_triggered', False) and st.session_state.file_bytes_io is None:
    st.warning("⚠️ Por favor, carregue um arquivo Excel válido primeiro antes de executar a análise.")

elif not st.session_state.get('main_analysis_triggered', False) and st.session_state.file_bytes_io is None: # Estado inicial
    st.info("👈 Por favor, carregue um arquivo Excel na barra lateral para começar a análise.")