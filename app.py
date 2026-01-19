import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# Chave para garantir que as mensagens carinhosas apareçam
app.secret_key = os.environ.get('SECRET_KEY', 'thamiris_araujo_estetica_2026')

SENHA_GESTAO = "8340"

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(database_url, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Criamos as tabelas se não existirem (sem apagar os dados salvos)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id SERIAL PRIMARY KEY,
            funcionario_id INTEGER REFERENCES funcionarios(id),
            entrada TIMESTAMP WITHOUT TIME ZONE,
            saida TIMESTAMP WITHOUT TIME ZONE
        );
    ''')
    # Garante que a Esther sempre esteja no banco para o ponto funcionar
    cur.execute("INSERT INTO funcionarios (nome) VALUES ('Esther Julia') ON CONFLICT (nome) DO NOTHING")
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    try:
        init_db() # Garante o banco pronto toda vez que abrir o site
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM funcionarios ORDER BY nome')
        funcionarios = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index.html', funcionarios=funcionarios)
    except Exception as e:
        return f"Erro ao carregar clínica: {e}"

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    funcionario_id = request.form.get('funcionario_id')
    tipo = request.form.get('tipo')
    agora = datetime.now()

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if tipo == 'entrada':
            cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (funcionario_id, agora))
            flash('Bom trabalho meu bem', 'success')
        elif tipo == 'saida':
            # Fecha o ponto mais recente que estiver aberto
            cur.execute('''
                UPDATE pontos SET saida = %s 
                WHERE funcionario_id = %s AND saida IS NULL
            ''', (agora, funcionario_id))
            flash('Bom descanso meu bem', 'success')
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'Erro ao registrar: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != SENHA_GESTAO:
        return "Acesso negado", 403
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Query revisada para evitar o erro de coluna na gestão
        cur.execute('''
            SELECT f.nome, p.entrada, p.saida
            FROM funcionarios f
            JOIN pontos p ON f.id = p.funcionario_id
            ORDER BY p.entrada DESC
        ''')
        pontos = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('painel_gestao.html', pontos=pontos)
    except Exception as e:
        return f"Erro na gestão: {e}"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)