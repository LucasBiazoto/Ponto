import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'thamiris_araujo_2026'

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(database_url, sslmode='require')

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS funcionarios (id SERIAL PRIMARY KEY, nome TEXT NOT NULL UNIQUE);')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pontos (
                id SERIAL PRIMARY KEY,
                funcionario_id INTEGER REFERENCES funcionarios(id),
                entrada TIMESTAMP WITHOUT TIME ZONE,
                saida TIMESTAMP WITHOUT TIME ZONE
            );
        ''')
        cur.execute("INSERT INTO funcionarios (nome) VALUES ('Esther Julia') ON CONFLICT (nome) DO NOTHING")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Aguardando banco: {e}")

@app.route('/')
def index():
    try:
        init_db()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM funcionarios ORDER BY nome')
        funcionarios = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('index.html', funcionarios=funcionarios)
    except Exception:
        # Se o banco der erro, ainda mostra o site (mas sem nomes) para o visual não sumir
        return render_template('index.html', funcionarios=[{'id': 1, 'nome': 'Esther Julia'}])

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    funcionario_id = request.form.get('funcionario_id')
    tipo = request.form.get('tipo')
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if tipo == 'entrada':
            cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (funcionario_id, datetime.now()))
            flash('Bom trabalho meu bem', 'success')
        else:
            cur.execute('UPDATE pontos SET saida = %s WHERE funcionario_id = %s AND saida IS NULL', (datetime.now(), funcionario_id))
            flash('Bom descanso meu bem', 'success')
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != "8340":
        return "Acesso negado", 403
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT f.nome, p.entrada, p.saida FROM funcionarios f JOIN pontos p ON f.id = p.funcionario_id ORDER BY p.entrada DESC')
        pontos = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('painel_gestao.html', pontos=pontos)
    except Exception as e:
        return f"Erro na gestão: {e}"

if __name__ == '__main__':
    app.run(debug=True)