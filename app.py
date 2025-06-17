import os
import io
import uuid
import pandas as pd
from flask import Flask, render_template, request, url_for, jsonify, send_from_directory, send_file, session, redirect
from werkzeug.utils import secure_filename
from flask_babel import Babel, _
from faturamento_forecast_class import FaturamentoForecast

app = Flask(__name__)

# --- CONFIGURAÇÕES DA APLICAÇÃO ---
app.secret_key = 'uma-chave-secreta-muito-dificil-de-adivinhar'
app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
babel = Babel()

def get_locale():
    return session.get('language', request.accept_languages.best_match(['pt', 'es', 'en']))

babel.init_app(app, locale_selector=get_locale)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- ROTAS DA APLICAÇÃO ---
@app.route('/language/<lang>')
def set_language(lang=None):
    session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files or request.files['file'].filename == '':
        return redirect(request.url)

    file = request.files['file']
    file_id = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    file.seek(0)
    file.save(file_path)

    file.seek(0)
    file_bytes = io.BytesIO(file.read())
    
    # Instancia a classe de análise, passando os nomes das colunas e o tradutor
    forecast_instance = FaturamentoForecast(
        file_input=file_bytes,
        coluna_data=request.form.get('col_data', 'EMISSÃO'),
        coluna_valor=request.form.get('col_valor', 'VALOR TOTAL'),
        coluna_produto=request.form.get('col_prod', 'DESCRIÇÃO MATERIAL'),
        coluna_cliente=request.form.get('col_cli', 'RAZÃO SOCIAL CLIENTE'),
        translator=_
    )
    
    # Coleta os parâmetros do formulário e converte os tipos de dados
    pipeline_params = {k: v for k, v in request.form.items()}
    pipeline_params['test_ratio'] = float(pipeline_params.get('test_ratio', 0.2))
    pipeline_params['periodos_forecast'] = int(pipeline_params.get('periodos_forecast', 12))
    pipeline_params['prophet_changepoint_prior_scale'] = float(pipeline_params.get('prophet_changepoint_prior_scale', 0.65))
    pipeline_params['prophet_seasonality_prior_scale'] = float(pipeline_params.get('prophet_seasonality_prior_scale', 25.0))
    
    results = forecast_instance.executar_pipeline_completo(**pipeline_params)
    
    # Salva o DataFrame da previsão para permitir o download futuro
    if results.get('previsao_futura_df') is not None and not results['previsao_futura_df'].empty:
        # Usa o DataFrame interno (não traduzido) para salvar
        internal_df_path = os.path.join(app.config['UPLOAD_FOLDER'], f"forecast_{file_id}.csv")
        results['previsao_futura_df_interno'].to_csv(internal_df_path, index=True)

    return render_template('results.html', results=results, file_id=file_id)

@app.route('/download/csv/<file_id>')
def download_csv(file_id):
    forecast_filename = f"forecast_{file_id}.csv"
    return send_from_directory(app.config['UPLOAD_FOLDER'], forecast_filename, as_attachment=True, download_name='previsao.csv')

@app.route('/download/xlsx/<file_id>')
def download_xlsx(file_id):
    forecast_filename = f"forecast_{file_id}.csv"
    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], forecast_filename)
    if not os.path.exists(csv_path):
        return _("Arquivo não encontrado."), 404
    df = pd.read_csv(csv_path, index_col=0)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name=_('Previsao'))
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='previsao_faturamento.xlsx'
    )

@app.route('/api/compare_products', methods=['POST'])
def compare_products():
    data = request.get_json()
    product_1 = data.get('product_1')
    product_2 = data.get('product_2')
    file_id = data.get('file_id')

    if not all([product_1, product_2, file_id]):
        return jsonify({'success': False, 'message': _('Informações ausentes.')}), 400
    if product_1 == product_2:
        return jsonify({'success': False, 'message': _('Por favor, selecione dois produtos diferentes.')}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': _('Arquivo de dados não encontrado.')}), 404
        
    forecast_instance = FaturamentoForecast(
        file_input=file_path, 
        coluna_data=session.get('col_data', 'EMISSÃO'), # Recupera da sessão ou usa padrão
        coluna_valor=session.get('col_valor', 'VALOR TOTAL'), 
        coluna_produto=session.get('col_prod', 'DESCRIÇÃO MATERIAL'), 
        coluna_cliente=session.get('col_cli', 'RAZÃO SOCIAL CLIENTE'),
        translator=_
    )
    forecast_instance.carregar_dados() 
    
    plot_json_1, plot_json_2 = forecast_instance.comparar_previsao_produtos(
        nome_produto_1=product_1, nome_produto_2=product_2
    )
    
    if plot_json_1 and plot_json_2:
        return jsonify({'success': True, 'plot_json_1': plot_json_1, 'plot_json_2': plot_json_2})
    else:
        return jsonify({'success': False, 'message': _('Não foi possível gerar o gráfico de comparação.')})

if __name__ == '__main__':
    app.run(debug=True)