import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='historico.db'):
        self.db_name = db_name
        self.criar_tabelas()

    def criar_tabelas(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabela para previsões
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS previsoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_criacao TIMESTAMP,
            nome_arquivo TEXT,
            periodo_forecast INTEGER,
            test_ratio REAL,
            prophet_changepoint_prior_scale REAL,
            prophet_seasonality_prior_scale REAL,
            coluna_data TEXT,
            coluna_valor TEXT,
            coluna_produto TEXT,
            coluna_cliente TEXT,
            arquivo_id TEXT
        )
        ''')
        
        # Tabela para comparações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comparacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_criacao TIMESTAMP,
            produto1 TEXT,
            produto2 TEXT,
            arquivo_id TEXT,
            coluna_data TEXT,
            coluna_valor TEXT,
            coluna_produto TEXT,
            coluna_cliente TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        self.migrate_db()

    def migrate_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Verifica se as colunas existem na tabela previsoes
        cursor.execute("PRAGMA table_info(previsoes)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        # Adiciona as novas colunas se não existirem
        novas_colunas = {
            'coluna_data': 'TEXT',
            'coluna_valor': 'TEXT',
            'coluna_produto': 'TEXT',
            'coluna_cliente': 'TEXT',
            'arquivo_id': 'TEXT'
        }
        
        for coluna, tipo in novas_colunas.items():
            if coluna not in colunas:
                cursor.execute(f'ALTER TABLE previsoes ADD COLUMN {coluna} {tipo}')
        
        # Verifica se as colunas existem na tabela comparacoes
        cursor.execute("PRAGMA table_info(comparacoes)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        # Adiciona as novas colunas se não existirem
        novas_colunas = {
            'coluna_data': 'TEXT',
            'coluna_valor': 'TEXT',
            'coluna_produto': 'TEXT',
            'coluna_cliente': 'TEXT'
        }
        
        for coluna, tipo in novas_colunas.items():
            if coluna not in colunas:
                cursor.execute(f'ALTER TABLE comparacoes ADD COLUMN {coluna} {tipo}')
        
        conn.commit()
        conn.close()

    def salvar_previsao(self, nome_arquivo, periodo_forecast, test_ratio, 
                       prophet_changepoint_prior_scale, prophet_seasonality_prior_scale,
                       coluna_data, coluna_valor, coluna_produto, coluna_cliente, arquivo_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO previsoes (data_criacao, nome_arquivo, periodo_forecast, 
                             test_ratio, prophet_changepoint_prior_scale, 
                             prophet_seasonality_prior_scale, coluna_data, coluna_valor,
                             coluna_produto, coluna_cliente, arquivo_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), nome_arquivo, periodo_forecast, test_ratio,
              prophet_changepoint_prior_scale, prophet_seasonality_prior_scale,
              coluna_data, coluna_valor, coluna_produto, coluna_cliente, arquivo_id))
        previsao_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return previsao_id

    def salvar_comparacao(self, produto1, produto2, arquivo_id, coluna_data, coluna_valor,
                         coluna_produto, coluna_cliente):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO comparacoes (data_criacao, produto1, produto2, arquivo_id,
                               coluna_data, coluna_valor, coluna_produto, coluna_cliente)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), produto1, produto2, arquivo_id,
              coluna_data, coluna_valor, coluna_produto, coluna_cliente))
        
        conn.commit()
        conn.close()

    def obter_historico_previsoes(self, limite=10):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, data_criacao, nome_arquivo, periodo_forecast, test_ratio,
               prophet_changepoint_prior_scale, prophet_seasonality_prior_scale,
               coluna_data, coluna_valor, coluna_produto, coluna_cliente, arquivo_id
        FROM previsoes
        ORDER BY data_criacao DESC
        LIMIT ?
        ''', (limite,))
        
        previsoes = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'data': row[1],
            'arquivo': row[2],
            'periodo': row[3],
            'test_ratio': row[4],
            'changepoint_scale': row[5],
            'seasonality_scale': row[6],
            'coluna_data': row[7],
            'coluna_valor': row[8],
            'coluna_produto': row[9],
            'coluna_cliente': row[10],
            'arquivo_id': row[11]
        } for row in previsoes]

    def obter_historico_comparacoes(self, limite=10):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, data_criacao, produto1, produto2, arquivo_id,
               coluna_data, coluna_valor, coluna_produto, coluna_cliente
        FROM comparacoes
        ORDER BY data_criacao DESC
        LIMIT ?
        ''', (limite,))
        
        comparacoes = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'data': row[1],
            'produto1': row[2],
            'produto2': row[3],
            'arquivo_id': row[4],
            'coluna_data': row[5],
            'coluna_valor': row[6],
            'coluna_produto': row[7],
            'coluna_cliente': row[8]
        } for row in comparacoes]

    def obter_previsao_por_id(self, previsao_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, data_criacao, nome_arquivo, periodo_forecast, test_ratio,
               prophet_changepoint_prior_scale, prophet_seasonality_prior_scale,
               coluna_data, coluna_valor, coluna_produto, coluna_cliente, arquivo_id
        FROM previsoes
        WHERE id = ?
        ''', (previsao_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'data': row[1],
                'arquivo': row[2],
                'periodo': row[3],
                'test_ratio': row[4],
                'changepoint_scale': row[5],
                'seasonality_scale': row[6],
                'coluna_data': row[7],
                'coluna_valor': row[8],
                'coluna_produto': row[9],
                'coluna_cliente': row[10],
                'arquivo_id': row[11]
            }
        return None

    def obter_comparacao_por_id(self, comparacao_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, data_criacao, produto1, produto2, arquivo_id,
               coluna_data, coluna_valor, coluna_produto, coluna_cliente
        FROM comparacoes
        WHERE id = ?
        ''', (comparacao_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'data': row[1],
                'produto1': row[2],
                'produto2': row[3],
                'arquivo_id': row[4],
                'coluna_data': row[5],
                'coluna_valor': row[6],
                'coluna_produto': row[7],
                'coluna_cliente': row[8]
            }
        return None

    def deletar_previsao(self, previsao_id):
        print(f"[DEBUG] Deletando previsao ID: {previsao_id} do banco: {self.db_name}")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM previsoes WHERE id = ?', (previsao_id,))
        conn.commit()
        conn.close()

    def deletar_comparacao(self, comparacao_id):
        print(f"[DEBUG] Deletando comparacao ID: {comparacao_id} do banco: {self.db_name}")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM comparacoes WHERE id = ?', (comparacao_id,))
        conn.commit()
        conn.close() 