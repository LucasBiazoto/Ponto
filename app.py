import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
SP_TZ = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    try:
        url = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url, sslmode='require')
    except: return None

@app.route('/')
def index():
    # Garante Esther Julia fixa na tela inicial
    return render_template('index.html', funcionarios=[{'id': 1, 'nome': 'Esther Julia'}])

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    fid, tipo = request.form.get('funcionario_id'), request.form.get('tipo')
    agora = datetime.now(SP_TZ)
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        if tipo == 'entrada':
            cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (fid, agora))
            flash('Bom trabalho meu bem 🌸', 'success')
        else:
            cur.execute('UPDATE pontos SET saida = %s WHERE funcionario_id = %s AND saida IS NULL', (agora, fid))
            flash('Bom descanso meu bem ✨', 'success')
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != '8340': return "Acesso Negado", 403
    mes = request.args.get('mes')
    conn = get_db_connection()
    pontos = []
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = "SELECT p.id, f.nome, p.entrada, p.saida FROM funcionarios f JOIN pontos p ON f.id = p.funcionario_id"
        if mes: query += f" WHERE EXTRACT(MONTH FROM p.entrada) = {mes}"
        cur.execute(query + " ORDER BY p.entrada DESC")
        pontos = cur.fetchall()
        cur.close()
        conn.close()
    return render_template('painel_gestao.html', pontos=pontos)

@app.route('/adicionar_manual', methods=['POST'])
def adicionar_manual():
    fid, ent, sai = request.form.get('funcionario_id'), request.form.get('entrada'), request.form.get('saida')
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO pontos (funcionario_id, entrada, saida) VALUES (%s, %s, %s)', (fid, ent, sai if sai else None))
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor(); cur.execute('DELETE FROM pontos WHERE id = %s', (id,)); conn.commit(); cur.close(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))