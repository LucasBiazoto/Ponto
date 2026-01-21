import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_secret_2026'

def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url, sslmode='require')
    except:
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
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
        except: pass

@app.route('/')
def index():
    init_db()
    funcionarios = [{'id': 1, 'nome': 'Esther Julia'}]
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT * FROM funcionarios ORDER BY nome')
            db_funcs = cur.fetchall()
            if db_funcs: funcionarios = db_funcs
            cur.close()
            conn.close()
        except: pass
    return render_template('index.html', funcionarios=funcionarios)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    fid = request.form.get('funcionario_id')
    tipo = request.form.get('tipo')
    agora = datetime.now()
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            if tipo == 'entrada':
                cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (fid, agora))
                flash('Bom trabalho meu bem', 'success')
            else:
                cur.execute('UPDATE pontos SET saida = %s WHERE funcionario_id = %s AND saida IS NULL', (agora, fid))
                flash('Bom descanso meu bem', 'success')
            conn.commit()
            cur.close()
            conn.close()
        except:
            flash('Erro ao salvar ponto.', 'danger')
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    # VALIDAÇÃO DE SENHA OBRIGATÓRIA
    senha = request.args.get('senha')
    if senha != "8340":
        flash("Acesso Negado: Senha incorreta.", "danger")
        return redirect(url_for('index'))
        
    pontos = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Query que traz as informações completas do menu de gestão
            cur.execute('''
                SELECT f.nome, p.entrada, p.saida 
                FROM funcionarios f 
                LEFT JOIN pontos p ON f.id = p.funcionario_id 
                ORDER BY p.entrada DESC NULLS LAST
            ''')
            pontos = cur.fetchall()
            cur.close()
            conn.close()
        except: pass
            
    return render_template('painel_gestao.html', pontos=pontos)

if __name__ == '__main__':
    app.run(debug=True)