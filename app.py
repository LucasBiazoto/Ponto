import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# A chave secreta é essencial para as mensagens de "bom trabalho" aparecerem
app.secret_key = os.environ.get('SECRET_KEY', 'thamiris_araujo_secret_key')

SENHA_GESTAO = "8340"

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    # Ajuste para o Render aceitar a conexão profissional
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(database_url)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
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
            entrada TIMESTAMP,
            saida TIMESTAMP
        );
    ''')
    # Garante que a Esther Julia esteja sempre no sistema
    cur.execute("INSERT INTO funcionarios (nome) VALUES ('Esther Julia') ON CONFLICT DO NOTHING")
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM funcionarios ORDER BY nome')
        funcionarios = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index.html', funcionarios=funcionarios)
    except Exception as e:
        return f"Erro ao carregar: {e}", 500

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    funcionario_id = request.form.get('funcionario_id')
    tipo = request.form.get('tipo')
    # O PostgreSQL exige este formato exato para confirmar o registro
    agora = datetime.now()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if tipo == 'entrada':
            cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (funcionario_id, agora))
            flash('Bom trabalho meu bem', 'success')
        elif tipo == 'saida':
            # Atualiza o último ponto em aberto
            cur.execute('''
                UPDATE pontos SET saida = %s 
                WHERE funcionario_id = %s AND saida IS NULL
            ''', (agora, funcionario_id))
            flash('Bom descanso meu bem', 'success')
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != SENHA_GESTAO:
        return "Acesso negado", 403

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Busca os pontos e calcula as horas para o relatório
    cur.execute('''
        SELECT f.nome, p.entrada, p.saida,
        CASE WHEN p.saida IS NOT NULL THEN 
        ROUND(CAST(EXTRACT(EPOCH FROM (p.saida - p.entrada))/3600 AS NUMERIC), 2)
        ELSE 0 END as horas_duracao
        FROM funcionarios f
        JOIN pontos p ON f.id = p.funcionario_id
        ORDER BY p.entrada DESC
    ''')
    pontos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('painel_gestao.html', pontos=pontos)

@app.route('/init_db')
def force_init():
    init_db()
    return "Sistema da Dra Thamiris inicializado!"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)