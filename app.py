import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'thamiris_araujo_estetica_2026'
SP_TZ = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    try:
        url = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url, sslmode='require')
    except: return None

@app.route('/')
def index():
    # Esther Julia sempre fixa na tela
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
    # Valida a senha direto na URL (ex: /painel_gestao?senha=8340)
    if request.args.get('senha') != '8340':
        return "Acesso Negado", 403
        
    pontos = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('''
                SELECT p.id, f.nome, p.entrada, p.saida 
                FROM funcionarios f 
                JOIN pontos p ON f.id = p.funcionario_id 
                ORDER BY p.entrada DESC
            ''')
            pontos = cur.fetchall()
            cur.close()
            conn.close()
        except: pass
    return render_template('painel_gestao.html', pontos=pontos)

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
    # Retorna ao painel mantendo a senha na URL para não dar erro de acesso
    return redirect(url_for('painel_gestao', senha='8340'))

if __name__ == '__main__':
    app.run(debug=True)