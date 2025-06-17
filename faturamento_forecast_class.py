import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from prophet import Prophet
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
import io
import traceback

warnings.filterwarnings('ignore')

class FaturamentoForecast:
    def __init__(self, file_input, coluna_data, coluna_valor, coluna_produto, coluna_cliente, translator=None):
        # Armazena os nomes das colunas fornecidos pelo usuário
        self.user_coluna_data = coluna_data
        self.user_coluna_valor = coluna_valor
        self.user_coluna_produto = coluna_produto
        self.user_coluna_cliente = coluna_cliente
        
        # Inicializa os nomes de colunas que serão realmente usados após a verificação
        self.coluna_data = None
        self.coluna_valor = None
        self.coluna_produto = None
        self.coluna_cliente = None
        
        self.file_input = file_input
        # Define um tradutor padrão (que não faz nada) se nenhum for passado
        self._ = translator if translator is not None else lambda s: s
        self.df_raw = None
        self.df_agregado = None
        self.modelo_prophet = None
        self.metricas = {}
        self.previsoes_futuras_df = None # DataFrame interno com nomes de coluna padrão
        self.top_produtos_list = []

    def carregar_dados(self):
        try:
            print("\n--- 1. Carregando dados ---")
            if isinstance(self.file_input, io.BytesIO): self.df_raw = pd.read_excel(self.file_input)
            else: self.df_raw = pd.read_excel(self.file_input)
            
            # Limpa os nomes das colunas no DataFrame (remove espaços extras)
            self.df_raw.columns = [str(c).strip() for c in self.df_raw.columns]
            
            # Função auxiliar segura para encontrar o nome real da coluna, ignorando maiúsculas/minúsculas
            def find_actual_column_name(user_provided_name, df_columns):
                if not user_provided_name: return None
                for col_name in df_columns:
                    if col_name.lower() == user_provided_name.lower():
                        print(f"   Coluna '{user_provided_name}' encontrada como '{col_name}' no arquivo.")
                        return col_name
                print(f"   AVISO: A coluna especificada '{user_provided_name}' não foi encontrada.")
                return user_provided_name

            all_df_columns = self.df_raw.columns
            self.coluna_data = find_actual_column_name(self.user_coluna_data, all_df_columns)
            self.coluna_valor = find_actual_column_name(self.user_coluna_valor, all_df_columns)
            self.coluna_produto = find_actual_column_name(self.user_coluna_produto, all_df_columns)
            self.coluna_cliente = find_actual_column_name(self.user_coluna_cliente, all_df_columns)

            if self.coluna_data not in all_df_columns or self.coluna_valor not in all_df_columns:
                raise ValueError("Colunas essenciais de Data ou Valor não foram encontradas.")

            self.df_raw[self.coluna_data] = pd.to_datetime(self.df_raw[self.coluna_data], errors='coerce')
            self.df_raw = self.df_raw.dropna(subset=[self.coluna_data])
            self.df_raw[self.coluna_valor] = pd.to_numeric(self.df_raw[self.coluna_valor], errors='coerce').fillna(0)
            
            print("   Dados carregados e tratados.")
            return self.df_raw
        except Exception as e:
            print(f"ERRO ao carregar dados: {e}")
            traceback.print_exc()
            return None

    def calcular_kpis_gerais(self):
        if self.df_raw is None: return {}
        print("\n--- Calculando KPIs Gerais ---")
        try:
            total_revenue = self.df_raw[self.coluna_valor].sum()
            total_transactions = len(self.df_raw)
            average_ticket = total_revenue / total_transactions if total_transactions > 0 else 0
            start_date = self.df_raw[self.coluna_data].min().strftime('%d/%m/%Y')
            end_date = self.df_raw[self.coluna_data].max().strftime('%d/%m/%Y')
            
            kpis = {
                'faturamento_total': f"R$ {total_revenue:,.2f}", 'ticket_medio': f"R$ {average_ticket:,.2f}",
                'total_transacoes': f"{total_transactions:,}", 'periodo_analise': f"{start_date} a {end_date}",
                'produtos_unicos': f"{self.df_raw[self.coluna_produto].nunique() if self.coluna_produto and self.coluna_produto in self.df_raw.columns else 'N/A'}",
                'clientes_unicos': f"{self.df_raw[self.coluna_cliente].nunique() if self.coluna_cliente and self.coluna_cliente in self.df_raw.columns else 'N/A'}",
            }
            return kpis
        except Exception as e:
            print(f"ERRO ao calcular KPIs: {e}")
            return {}
            
    def agregar_dados(self, freq='M'):
        if self.df_raw is None: return None
        try:
            df_para_agregar = self.df_raw.set_index(self.coluna_data)
            self.df_agregado = df_para_agregar.resample(freq)[self.coluna_valor].sum().to_frame()
            return self.df_agregado
        except Exception: return None

    def calcular_metricas(self, y_real, y_pred):
        return {'MAE': mean_absolute_error(y_real, y_pred), 'RMSE': np.sqrt(mean_squared_error(y_real, y_pred)), 'R²': r2_score(y_real, y_pred)}

    def plotar_previsoes_validacao(self, dados_treino_reais, dados_teste_reais, previsoes_teste, intervalo_confianca, modelo_nome):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dados_treino_reais.index, y=dados_treino_reais, mode='lines', name=self._('Histórico (Treino)'), line=dict(color='silver')))
        fig.add_trace(go.Scatter(x=dados_teste_reais.index, y=dados_teste_reais, mode='markers+lines', name=self._('Valores Reais (Teste)'), line=dict(color='#2ca02c')))
        fig.add_trace(go.Scatter(x=previsoes_teste.index, y=previsoes_teste, mode='lines', name=self._('Previsão %(modelo)s (Teste)') % {'modelo': modelo_nome}, line=dict(color='#ff7f0e', dash='dash')))
        if intervalo_confianca is not None:
            fig.add_trace(go.Scatter(x=intervalo_confianca.index, y=intervalo_confianca['IC_Superior'], mode='lines', line=dict(width=0), showlegend=False, hoverinfo='none'))
            fig.add_trace(go.Scatter(x=intervalo_confianca.index, y=intervalo_confianca['IC_Inferior'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 127, 14, 0.2)', name=self._('Intervalo de Confiança'), hoverinfo='none'))
        fig.update_layout(title=self._('Validação do Modelo %(modelo)s: Previsão vs. Real') % {'modelo': modelo_nome}, xaxis_title=self._('Data'), yaxis_title=self.coluna_valor, template='plotly_dark', height=600, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        return pio.to_html(fig, full_html=False, config={'displayModeBar': False})

    def plotar_previsao_futura(self, periodos, modelo_nome):
        if self.previsoes_futuras_df is None: return None
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.df_agregado.index, y=self.df_agregado[self.coluna_valor], mode='lines', name=self._('Histórico Completo'), line=dict(color='#1f77b4')))
        fig.add_trace(go.Scatter(x=self.previsoes_futuras_df.index, y=self.previsoes_futuras_df['Previsao'], mode='lines', name=self._('Previsão Futura'), line=dict(color='#ff7f0e', dash='dash')))
        fig.add_trace(go.Scatter(x=self.previsoes_futuras_df.index, y=self.previsoes_futuras_df['IC_Superior'], mode='lines', line=dict(width=0), showlegend=False, hoverinfo='none'))
        fig.add_trace(go.Scatter(x=self.previsoes_futuras_df.index, y=self.previsoes_futuras_df['IC_Inferior'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 127, 14, 0.2)', name=self._('Intervalo de Confiança'), hoverinfo='none'))
        fig.update_layout(title=self._('Previsão de %(valor)s (%(modelo)s) - Próximos %(n)s Períodos') % {'valor': self.coluna_valor, 'modelo': modelo_nome, 'n': periodos}, xaxis_title=self._('Data'), yaxis_title=self.coluna_valor, template='plotly_dark', height=600, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        return pio.to_html(fig, full_html=False, config={'displayModeBar': False})

    def fazer_previsao_futura_prophet(self, periodos=12):
        if self.modelo_prophet is None: return None, None
        
        future_dates_df = self.modelo_prophet.make_future_dataframe(periods=periodos, freq='MS')
        forecast = self.modelo_prophet.predict(future_dates_df)
        
        # Cria o DataFrame com nomes de coluna padrão para uso interno (plotagem, download)
        df_interno = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(columns={
            'ds': 'Data', 'yhat': 'Previsao', 'yhat_lower': 'IC_Inferior', 'yhat_upper': 'IC_Superior'
        }).set_index('Data').tail(periodos)
        
        # Armazena a versão interna com nomes padrão
        self.previsoes_futuras_df = df_interno

        # Gera o gráfico usando o DataFrame interno
        fig_futura_html = self.plotar_previsao_futura(periodos, 'Prophet')
        
        # Cria uma cópia com nomes traduzidos apenas para exibição na tabela HTML
        df_display = df_interno.copy()
        df_display.columns = [self._('Previsao'), self._('IC_Inferior'), self._('IC_Superior')]
        df_display.index.name = self._('Data')
        
        # --- CORREÇÃO AQUI: Retornando o DataFrame sem o reset_index() ---
        # Isso garante que o índice continue sendo as datas.
        return df_display, fig_futura_html
    
    def treinar_modelo_prophet(self, dados_teste_ratio=0.2, **prophet_kwargs):
        if self.df_agregado is None: return None, {}
        df_prophet = self.df_agregado.reset_index().rename(columns={self.coluna_data: 'ds', self.coluna_valor: 'y'})
        split_idx = int(len(df_prophet) * (1 - dados_teste_ratio))
        df_train, df_test = df_prophet.iloc[:split_idx], df_prophet.iloc[split_idx:]
        
        params_for_prophet = {
            'seasonality_mode': prophet_kwargs.get('prophet_seasonality_mode', 'additive'),
            'changepoint_prior_scale': float(prophet_kwargs.get('prophet_changepoint_prior_scale', 0.05)),
            'seasonality_prior_scale': float(prophet_kwargs.get('prophet_seasonality_prior_scale', 10.0))}
        
        self.modelo_prophet = Prophet(**params_for_prophet).fit(df_train)
        forecast_test = self.modelo_prophet.predict(df_test[['ds']].copy())
        results_test = pd.merge(df_test, forecast_test, on='ds')
        self.metricas = self.calcular_metricas(results_test['y'], results_test['yhat'])
        intervalo_conf_df = results_test[['ds', 'yhat_lower', 'yhat_upper']].rename(columns={'yhat_lower':'IC_Inferior', 'yhat_upper':'IC_Superior'}).set_index('ds')
        
        fig_validacao_html = self.plotar_previsoes_validacao(df_train.set_index('ds')['y'], results_test.set_index('ds')['y'], results_test.set_index('ds')['yhat'], intervalo_conf_df, 'Prophet')
        return self.modelo_prophet, {'validacao': fig_validacao_html}

    def comparar_previsao_produtos(self, nome_produto_1, nome_produto_2, freq='M', periodos=12):
        def _gerar_grafico_plotly(nome_produto):
            if not self.coluna_produto or self.coluna_produto not in self.df_raw.columns: return None
            df_prod = self.df_raw[self.df_raw[self.coluna_produto] == nome_produto].copy()
            if df_prod.empty: return None
            
            df_prod_agg = df_prod.set_index(self.coluna_data).resample(freq)[self.coluna_valor].sum().fillna(0)
            df_prophet = df_prod_agg.reset_index().rename(columns={self.coluna_data: 'ds', self.coluna_valor: 'y'})
            if len(df_prophet) < 5: return None
            
            m = Prophet(seasonality_mode='multiplicative').fit(df_prophet)
            future = m.make_future_dataframe(periods=periodos, freq='MS')
            forecast = m.predict(future)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', line=dict(width=0), hoverinfo="none", showlegend=False, fillcolor='rgba(131, 192, 232, 0.3)'))
            fig.add_trace(go.Scatter(name=self._('Intervalo de Confiança'), x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(131, 192, 232, 0.3)', hoverinfo="none"))
            fig.add_trace(go.Scatter(name=self._('Previsão'), x=forecast['ds'], y=forecast['yhat'], mode='lines', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(name=self._('Histórico'), x=df_prophet['ds'], y=df_prophet['y'], mode='lines'))
            fig.update_layout(title=self._('Previsão para: %(produto)s') % {'produto': nome_produto[:30] + '...'}, xaxis_title=self._('Data'), yaxis_title=self._('Valor Total'), template='plotly_dark')
            return pio.to_json(fig)

        plot_json_1 = _gerar_grafico_plotly(nome_produto_1)
        plot_json_2 = _gerar_grafico_plotly(nome_produto_2)
        return plot_json_1, plot_json_2

    def executar_pipeline_completo(self, **kwargs):
        results = {
            'df_raw': None, 'df_agregado': None, 'modelo': None, 'metricas': {}, 'kpis_gerais': {}, 
            'validacao_fig': None, 'previsao_futura_df': None, 'previsao_futura_fig': None, 
            'top_produtos_list': [], 'previsao_futura_df_interno': None
        }
        try:
            results['df_raw'] = self.carregar_dados()
            if results['df_raw'] is None: raise ValueError("Erro no carregamento dos dados.")
            
            results['kpis_gerais'] = self.calcular_kpis_gerais()
            results['df_agregado'] = self.agregar_dados(freq=kwargs.get('freq_agg', 'M'))
            if results['df_agregado'] is None: raise ValueError("Erro na agregação dos dados.")

            if kwargs.get('modelo_tipo', 'prophet').lower() == 'prophet':
                modelo_treinado, figs_treinamento = self.treinar_modelo_prophet(
                    dados_teste_ratio=float(kwargs.get('test_ratio', 0.2)), **kwargs
                )
                results['validacao_fig'] = figs_treinamento.get('validacao')
                results['modelo'] = modelo_treinado
                results['metricas'] = self.metricas
                
                if modelo_treinado is not None:
                    df_display, fig_futura = self.fazer_previsao_futura_prophet(periodos=int(kwargs.get('periodos_forecast', 12)))
                    results['previsao_futura_df'] = df_display
                    results['previsao_futura_df_interno'] = self.previsoes_futuras_df
                    results['previsao_futura_fig'] = fig_futura

            if self.coluna_produto and self.coluna_produto in self.df_raw.columns:
                 results['top_produtos_list'] = self.df_raw.groupby(self.coluna_produto)[self.coluna_valor].sum().nlargest(20).index.tolist()

        except Exception as e:
            print(f"ERRO NO PIPELINE: {e}")
            traceback.print_exc()
        
        return results