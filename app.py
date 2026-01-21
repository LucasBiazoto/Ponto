import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret_2026'

def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url, sslmode='require')
    except:
        return None

@app.route('/')
def index():
    # Tenta pegar funcionários do banco, se falhar, cria uma lista manual para o site não ficar branco
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
    tipo = request.form.get('tipo')
    if tipo == 'entrada':
        flash('Bom trabalho meu bem', 'success')
    else:
        flash('Bom descanso meu bem', 'success')
    
    # Tenta salvar no banco em segundo plano
    conn = get_db_connection()
    if conn:
        try:
            fid = request.form.get('funcionario_id')
            cur = conn.cursor()
            if tipo == 'entrada':
                cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (fid, datetime.now()))
            else:
                cur.execute('UPDATE pontos SET saida = %s WHERE funcionario_id = %s AND saida IS NULL', (datetime.now(), fid))
            conn.commit()
            cur.close()
            conn.close()
        except: pass
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != "8340":
        return "Senha Incorreta", 403
    pontos = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT f.nome, p.entrada, p.saida FROM funcionarios f JOIN pontos p ON f.id = p.funcionario_id ORDER BY p.entrada DESC')
            pontos = cur.fetchall()
            cur.close()
            conn.close()
        except: pass
    return render_template('painel_gestao.html', pontos=pontos)

if __name__ == '__main__':
    app.run(debug=True)