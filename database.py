import os
import pandas as pd
import psycopg2

# Cole aqui a URL de conexão do Neon que copiou
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_eDd5hZTvwW3y@ep-red-sound-b533gioc-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

def obter_conexao():
    """Retorna a conexão com o banco de dados PostgreSQL no Neon."""
    return psycopg2.connect(DATABASE_URL)

def inicializar_banco():
    """Garante que todas as tabelas existem na nuvem do Neon."""
    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id SERIAL PRIMARY KEY,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            conta TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aportes (
            id SERIAL PRIMARY KEY,
            data TEXT,
            local_aplicacao TEXT,
            descricao TEXT,
            valor REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dividas (
            id SERIAL PRIMARY KEY,
            credor TEXT,
            valor_total REAL,
            juros_mensal REAL,
            status TEXT
        )
    """)

    conexao.commit()
    cursor.close()
    conexao.close()

def inserir_lancamento(data, tipo, categoria, descricao, valor, conta=""):
    """Insere um novo lançamento financeiro no Neon."""
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        """
        INSERT INTO lancamentos (data, tipo, categoria, descricao, valor, conta)
        VALUES (%s, %s, %s, %s, %s, %s)
    """,
        (data, tipo, categoria, descricao, float(valor), conta),
    )
    conexao.commit()
    cursor.close()
    conexao.close()