import os
import io
import uuid
import pandas as pd
from flask import Flask, render_template, request, url_for, jsonify, send_from_directory, send_file, session, redirect, flash
from werkzeug.utils import secure_filename
from flask_babel import Babel, _
from faturamento_forecast_class import FaturamentoForecast
from deep_translator import GoogleTranslator
import bleach
from functools import wraps
from datetime import datetime, timedelta
from database import Database
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- CONFIGURAÇÕES DA APLICAÇÃO ---
app.secret_key = 'uma-chave-secreta-muito-dificil-de-adivinhar'
app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
app.config['LANGUAGES'] = {
    'pt': 'Português',
    'en': 'English',
    'es': 'Español'
}
babel = Babel()

# Inicializa o banco de dados
db = Database(app.config.get('DATABASE', 'historico.db'))

def get_locale():
    return session.get('language', request.accept_languages.best_match(['pt', 'es', 'en']))

babel.init_app(app, locale_selector=get_locale)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def auto_translate(text, target_lang):
    if not text or target_lang == 'pt':
        return text
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception:
        return text

# Função para usar Babel se possível, senão tradução automática
from flask_babel import get_locale as babel_get_locale

def smart_translate(text):
    lang = str(babel_get_locale())
    translated = _(text)
    # Se não houver tradução (retorna igual ao original), tenta tradução automática
    if translated == text and lang != 'pt':
        return auto_translate(text, lang)
    return translated

# Função utilitária para sanitizar todos os campos de um dicionário
def sanitize_dict(data):
    return {k: bleach.clean(v, tags=[], attributes={}) if isinstance(v, str) else v for k, v in data.items()}

# Usuário inicial
USERS = {'admin': '123'}

def is_logged_in():
    return session.get('logged_in', False)

SESSION_TIMEOUT = 3600  # 1 hora em segundos
FLASH_MESSAGE_COOLDOWN = 5 # 5 segundos de cooldown para mensagens flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # Limpa qualquer mensagem flash existente
            session.pop('_flashes', None)
            flash(_('Você deve estar logado para prosseguir.'), 'warning')
            return redirect(url_for('home1'))
        # Timeout de sessão
        last_active = session.get('last_active')
        now = datetime.utcnow().timestamp()
        if last_active and now - last_active > SESSION_TIMEOUT:
            session.clear()
            flash(_('Sessão expirada. Faça login novamente.'), 'warning')
            return redirect(url_for('login'))
        session['last_active'] = now
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if USERS.get(username) == password:
            session['logged_in'] = True
            session['username'] = username
            session['last_active'] = datetime.utcnow().timestamp()
            return redirect(url_for('admin_area'))
        else:
            error = _('Usuário ou senha inválidos.')
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home1'))

# --- ROTAS DA APLICAÇÃO ---
@app.route('/language/<lang>')
def set_language(lang=None):
    if lang in app.config['LANGUAGES']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
@login_required
def index():
    # Obtém o histórico de previsões e comparações
    historico_previsoes = db.obter_historico_previsoes()
    historico_comparacoes = db.obter_historico_comparacoes()
    return render_template('index.html', 
                         historico_previsoes=historico_previsoes,
                         historico_comparacoes=historico_comparacoes)

@app.route('/home1')
def home1():
    product_categories = [
        {
            'name': 'Bombas e motores de engrenagens',
            'link': 'https://sohipren.com/pt/10-bombas-e-motores-de-engrenagens',
            'image': 'bombas-e-motores-de-engrenagens.jpg',
            'description': 'Soluções completas em bombas e motores de engrenagens para diversas aplicações industriais.'
        },
        {
            'name': 'Bombas de pistões',
            'link': 'https://sohipren.com/pt/11-bombas-de-pistoes',
            'image': 'bombas-de-pistoes.jpg',
            'description': 'Bombas de pistões de alta performance para sistemas hidráulicos de alta pressão.'
        },
        {
            'name': 'Vávulas óleo hidráulicas',
            'link': 'https://sohipren.com/pt/12-valvulas-oleo-hidraulicas',
            'image': 'valvulas-oleo-hidraulicas.jpg',
            'description': 'Linha completa de válvulas para controle e direcionamento de fluxo em sistemas hidráulicos.'
        },
        {
            'name': 'Motores orbitais',
            'link': 'https://sohipren.com/pt/13-motores-orbitais',
            'image': 'motores-orbitais.jpg',
            'description': 'Motores orbitais de alta eficiência para aplicações que exigem precisão e confiabilidade.'
        },
        {
            'name': 'Direções hidrostáticas',
            'link': 'https://sohipren.com/pt/14-direcoes-hidrostaticas',
            'image': 'direcoes-hidrostaticas.jpg',
            'description': 'Sistemas de direção hidrostática para veículos industriais e agrícolas.'
        },
        {
            'name': 'Mangueiras óleo-hidráulicas',
            'link': 'https://sohipren.com/pt/15-mangueiras-oleo-hidraulicas',
            'image': 'mangueiras-oleo-hidraulicas.jpg',
            'description': 'Mangueiras de alta pressão para conexão e transferência de fluidos hidráulicos.'
        },
        {
            'name': 'Tomadas de força',
            'link': 'https://sohipren.com/pt/16-tomadas-de-forca',
            'image': 'tomadas-de-forca.jpg',
            'description': 'Tomadas de força para transmissão de potência em equipamentos industriais.'
        },
        {
            'name': 'Servos de direção',
            'link': 'https://sohipren.com/pt/17-servos-de-direcao',
            'image': 'servos-de-direcao.jpg',
            'description': 'Servos de direção para controle preciso em sistemas hidráulicos.'
        },
        {
            'name': 'Desenvolvimento de soluções hidráulicas',
            'link': 'https://sohipren.com/pt/18-desenvolvimento-de-solucoes-hidraulicas',
            'image': 'desenvolvimento-de-solucoes-hidraulicas.jpg',
            'description': 'Soluções personalizadas em hidráulica para atender às necessidades específicas do seu projeto.'
        },
        {
            'name': 'Peças e acessórios',
            'link': 'https://sohipren.com/pt/19-pecas-e-acessorios',
            'image': 'revisao-caoa.jpg',
            'description': 'Peças e acessórios para manutenção e reparo de sistemas hidráulicos.'
        }
    ]
    return render_template('home1.html', categories=product_categories)

@app.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    if request.method == 'GET':
        return render_template('analyze.html')
        
    if 'file' not in request.files or request.files['file'].filename == '':
        return redirect(request.url)

    file = request.files['file']
    file_id = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    file.seek(0)
    file.save(file_path)

    file.seek(0)
    file_bytes = io.BytesIO(file.read())
    
    # Sanitizar entradas do formulário
    sanitized_form = sanitize_dict(request.form)
    
    forecast_instance = FaturamentoForecast(
        file_input=file_bytes,
        coluna_data=sanitized_form.get('col_data', 'EMISSÃO'),
        coluna_valor=sanitized_form.get('col_valor', 'VALOR TOTAL'),
        coluna_produto=sanitized_form.get('col_prod', 'DESCRIÇÃO MATERIAL'),
        coluna_cliente=sanitized_form.get('col_cli', 'RAZÃO SOCIAL CLIENTE'),
        translator=smart_translate
    )
    
    pipeline_params = {k: v for k, v in sanitized_form.items()}
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
        
        # Salva no histórico
        db.salvar_previsao(
            nome_arquivo=secure_filename(file.filename),
            periodo_forecast=pipeline_params['periodos_forecast'],
            test_ratio=pipeline_params['test_ratio'],
            prophet_changepoint_prior_scale=pipeline_params['prophet_changepoint_prior_scale'],
            prophet_seasonality_prior_scale=pipeline_params['prophet_seasonality_prior_scale'],
            coluna_data=sanitized_form.get('col_data', 'EMISSÃO'),
            coluna_valor=sanitized_form.get('col_valor', 'VALOR TOTAL'),
            coluna_produto=sanitized_form.get('col_prod', 'DESCRIÇÃO MATERIAL'),
            coluna_cliente=sanitized_form.get('col_cli', 'RAZÃO SOCIAL CLIENTE'),
            arquivo_id=file_id
        )

    return render_template('results.html', results=results, file_id=file_id)

@app.route('/download/csv/<file_id>')
def download_csv(file_id):
    forecast_filename = f"forecast_{file_id}.csv"
    return send_from_directory(app.config['UPLOAD_FOLDER'], forecast_filename, as_attachment=True, download_name=_('previsao.csv'))

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
        download_name=_('previsao_faturamento.xlsx')
    )

def buscar_primeira_imagem_google(query):
    # Sempre adiciona 'SOHIPREN' antes do termo de pesquisa
    query_modificada = f"SOHIPREN {query}"
    url = f"https://www.google.com/search?tbm=isch&q={query_modificada.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    imagens = soup.find_all('img')
    for img in imagens:
        src = img.get('src')
        if src and src.startswith('http'):
            return src
    return None

@app.route('/api/compare_products', methods=['POST'])
def compare_products():
    data = request.get_json()
    sanitized_data = sanitize_dict(data)
    product_1 = sanitized_data.get('product_1')
    product_2 = sanitized_data.get('product_2')
    file_id = sanitized_data.get('file_id')

    if not all([product_1, product_2, file_id]):
        return jsonify({'success': False, 'message': _('Informações ausentes.')}), 400
    if product_1 == product_2:
        return jsonify({'success': False, 'message': _('Por favor, selecione dois produtos diferentes.')}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': _('Arquivo de dados não encontrado.')}), 404
        
    forecast_instance = FaturamentoForecast(
        file_input=file_path, 
        coluna_data=session.get('col_data', 'EMISSÃO'),
        coluna_valor=session.get('col_valor', 'VALOR TOTAL'), 
        coluna_produto=session.get('col_prod', 'DESCRIÇÃO MATERIAL'), 
        coluna_cliente=session.get('col_cli', 'RAZÃO SOCIAL CLIENTE'),
        translator=smart_translate
    )
    forecast_instance.carregar_dados() 
    
    plot_json_1, plot_json_2 = forecast_instance.comparar_previsao_produtos(
        nome_produto_1=product_1, nome_produto_2=product_2
    )

    # Buscar imagens em tempo real
    img1 = buscar_primeira_imagem_google(product_1)
    img2 = buscar_primeira_imagem_google(product_2)
    
    if plot_json_1 and plot_json_2:
        db.salvar_comparacao(
            produto1=product_1,
            produto2=product_2,
            arquivo_id=file_id,
            coluna_data=session.get('col_data', 'EMISSÃO'),
            coluna_valor=session.get('col_valor', 'VALOR TOTAL'),
            coluna_produto=session.get('col_prod', 'DESCRIÇÃO MATERIAL'),
            coluna_cliente=session.get('col_cli', 'RAZÃO SOCIAL CLIENTE')
        )
        return jsonify({'success': True, 'plot_json_1': plot_json_1, 'plot_json_2': plot_json_2, 'img1': img1, 'img2': img2})
    else:
        return jsonify({'success': False, 'message': _('Não foi possível gerar o gráfico de comparação.')})

@app.route('/api/previsao/<int:previsao_id>')
@login_required
def obter_detalhes_previsao(previsao_id):
    previsao = db.obter_previsao_por_id(previsao_id)
    if not previsao:
        return jsonify({'success': False, 'message': _('Previsão não encontrada.')}), 404
    return jsonify({'success': True, 'previsao': previsao})

@app.route('/api/comparacao/<int:comparacao_id>')
@login_required
def obter_detalhes_comparacao(comparacao_id):
    comparacao = db.obter_comparacao_por_id(comparacao_id)
    if not comparacao:
        return jsonify({'success': False, 'message': _('Comparação não encontrada.')}), 404
    return jsonify({'success': True, 'comparacao': comparacao})

@app.route('/api/refazer_comparacao/<int:comparacao_id>', methods=['POST'])
@login_required
def refazer_comparacao(comparacao_id):
    comparacao = db.obter_comparacao_por_id(comparacao_id)
    if not comparacao:
        return jsonify({'success': False, 'message': _('Comparação não encontrada.')}), 404

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], comparacao['arquivo_id'])
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': _('Arquivo de dados não encontrado.')}), 404

    forecast_instance = FaturamentoForecast(
        file_input=file_path,
        coluna_data=comparacao['coluna_data'],
        coluna_valor=comparacao['coluna_valor'],
        coluna_produto=comparacao['coluna_produto'],
        coluna_cliente=comparacao['coluna_cliente'],
        translator=smart_translate
    )
    forecast_instance.carregar_dados()

    plot_json_1, plot_json_2 = forecast_instance.comparar_previsao_produtos(
        nome_produto_1=comparacao['produto1'],
        nome_produto_2=comparacao['produto2']
    )

    if plot_json_1 and plot_json_2:
        return jsonify({
            'success': True,
            'plot_json_1': plot_json_1,
            'plot_json_2': plot_json_2,
            'produto1': comparacao['produto1'],
            'produto2': comparacao['produto2']
        })
    else:
        return jsonify({'success': False, 'message': _('Não foi possível gerar o gráfico de comparação.')})

@app.route('/admin')
@login_required
def admin_area():
    return redirect(url_for('index'))

@app.route('/api/delete_previsao/<int:previsao_id>', methods=['POST'])
@login_required
def delete_previsao(previsao_id):
    try:
        db.deletar_previsao(previsao_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete_comparacao/<int:comparacao_id>', methods=['POST'])
@login_required
def delete_comparacao(comparacao_id):
    try:
        db.deletar_comparacao(comparacao_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    print("""
✅ Proteção XSS ativa: Entradas do usuário são sanitizadas com bleach.clean()
🛡️ Nunca use |safe em variáveis vindas do usuário sem sanitização!
🧪 Sugestão: Valide também no frontend para experiência mais segura.
""")
    app.run(debug=True, host='0.0.0.0') 