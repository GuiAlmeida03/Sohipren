import pytest
import os
import sys

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configura o ambiente de teste antes de cada teste"""
    # Cria diretório de uploads de teste se não existir
    test_uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'test_uploads')
    os.makedirs(test_uploads_dir, exist_ok=True)
    
    # Configura variáveis de ambiente de teste
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_APP'] = 'app.py'
    
    yield
    
    # Limpa arquivos de teste após cada teste
    if os.path.exists(test_uploads_dir):
        for file in os.listdir(test_uploads_dir):
            file_path = os.path.join(test_uploads_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Erro ao deletar {file_path}: {e}') 