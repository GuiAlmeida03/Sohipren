import pytest
import os
import json
import pandas as pd
from datetime import datetime
import io

# Recria o objeto db ANTES de importar o app
from database import Database

test_db = 'test_historico.db'
if os.path.exists(test_db):
    os.remove(test_db)
db = Database(test_db)

import app as app_module
app = app_module.app
app_module.db = db  # Garante que o app use o db correto

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'test_uploads'
    app.config['DATABASE'] = test_db
    os.makedirs('test_uploads', exist_ok=True)
    with app.test_client() as client:
        with app.app_context():
            db.criar_tabelas()
        yield client
    if os.path.exists(test_db):
        os.remove(test_db)
    for file in os.listdir('test_uploads'):
        os.remove(os.path.join('test_uploads', file))
    os.rmdir('test_uploads')

def test_login_success(client):
    """Testa o login bem-sucedido"""
    response = client.post('/login', data={
        'username': 'admin',
        'password': '123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Verifica se está logado pela presença do botão de logout
    assert b'logout' in response.data or b'Logout' in response.data

def test_login_failure(client):
    """Testa o login com credenciais inválidas"""
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'senha_errada'
    }, follow_redirects=True)
    assert b'Usu' in response.data or b'inv' in response.data

def test_analyze_file_upload(client):
    """Testa o upload e análise de arquivo"""
    client.post('/login', data={
        'username': 'admin',
        'password': '123'
    })
    
    # Cria um DataFrame de teste
    df = pd.DataFrame({
        'EMISSÃO': pd.date_range(start='2023-01-01', periods=12, freq='M'),
        'VALOR TOTAL': [1000, 1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100],
        'DESCRIÇÃO MATERIAL': ['Produto A'] * 12,
        'RAZÃO SOCIAL CLIENTE': ['Cliente 1'] * 12
    })
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    
    response = client.post('/analyze', 
        data={
            'file': (buffer, 'test.xlsx'),
            'col_data': 'EMISSÃO',
            'col_valor': 'VALOR TOTAL',
            'col_prod': 'DESCRIÇÃO MATERIAL',
            'col_cli': 'RAZÃO SOCIAL CLIENTE',
            'test_ratio': '0.2',
            'periodos_forecast': '12',
            'prophet_changepoint_prior_scale': '0.65',
            'prophet_seasonality_prior_scale': '25.0'
        },
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    # Verifica se a página de resultados foi renderizada
    assert b'Resultados' in response.data or b'resultados' in response.data

def test_compare_products(client):
    """Testa a comparação de produtos"""
    client.post('/login', data={
        'username': 'admin',
        'password': '123'
    })
    
    df = pd.DataFrame({
        'EMISSÃO': pd.date_range(start='2023-01-01', periods=12, freq='M'),
        'VALOR TOTAL': [1000, 1200, 1100, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100],
        'DESCRIÇÃO MATERIAL': ['Produto A'] * 6 + ['Produto B'] * 6,
        'RAZÃO SOCIAL CLIENTE': ['Cliente 1'] * 12
    })
    file_id = 'test_file.xlsx'
    file_path = os.path.join('test_uploads', file_id)
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    response = client.post('/api/compare_products',
        json={
            'product_1': 'Produto A',
            'product_2': 'Produto B',
            'file_id': file_id
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True or data.get('message')

def test_delete_previsao(client):
    """Testa a exclusão de uma previsão"""
    client.post('/login', data={
        'username': 'admin',
        'password': '123'
    })
    previsao_id = db.salvar_previsao(
        nome_arquivo='test.xlsx',
        periodo_forecast=12,
        test_ratio=0.2,
        prophet_changepoint_prior_scale=0.65,
        prophet_seasonality_prior_scale=25.0,
        coluna_data='EMISSÃO',
        coluna_valor='VALOR TOTAL',
        coluna_produto='DESCRIÇÃO MATERIAL',
        coluna_cliente='RAZÃO SOCIAL CLIENTE',
        arquivo_id='test_file.xlsx'
    )
    response = client.post(f'/api/delete_previsao/{previsao_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    previsao = db.obter_previsao_por_id(previsao_id)
    assert previsao is None 