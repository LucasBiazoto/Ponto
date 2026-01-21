import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'thamiris_araujo_estetica_premium'
SP_TZ = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    try:
        url = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url, sslmode='require')
    except: return None

@app.route('/')
def index():
    # GARANTE ESTHER JULIA SEMPRE PRESENTE
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
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(SP_TZ)
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        if tipo == 'entrada':
            cur.execute('INSERT INTO pontos (funcionario_id, entrada, latitude, longitude) VALUES (%s, %s, %s, %s)', 
                        (fid, agora, lat, lon))
            flash('Bom trabalho meu bem 🌸', 'success')
        else:
            cur.execute('UPDATE pontos SET saida = %s WHERE funcionario_id = %s AND saida IS NULL', (agora, fid))
            flash('Bom descanso meu bem ✨', 'success')
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        if request.form.get('senha') == '8340':
            return redirect(url_for('painel_gestao', auth='8340'))
        flash("Senha incorreta!", "danger")
    return render_template('login_admin.html')

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('auth') != '8340':
        return redirect(url_for('login_admin'))
    
    conn = get_db_connection()
    pontos = []
    if conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT p.id, f.nome, p.entrada, p.saida, p.latitude, p.longitude 
            FROM funcionarios f 
            JOIN pontos p ON f.id = p.funcionario_id 
            ORDER BY p.entrada DESC
        ''')
        pontos = cur.fetchall()
        cur.close()
        conn.close()
    return render_template('painel_gestao.html', pontos=pontos)

# NOVA FUNÇÃO: ADICIONAR MARCAÇÃO MANUAL (PARA QUEM ESQUECEU)
@app.route('/adicionar_manual', methods=['POST'])
def adicionar_manual():
    fid = request.form.get('funcionario_id')
    entrada = request.form.get('entrada')
    saida = request.form.get('saida')
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO pontos (funcionario_id, entrada, saida) VALUES (%s, %s, %s)', 
                    (fid, entrada, saida))
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('painel_gestao', auth='8340'))

# NOVA FUNÇÃO: ADICIONAR NOVA FUNCIONÁRIA (PARA PESSOAS NOVAS)
@app.route('/cadastrar_funcionaria', methods=['POST'])
def cadastrar_funcionaria():
    nome = request.form.get('nome')
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO funcionarios (nome) VALUES (%s) ON CONFLICT DO NOTHING', (nome,))
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('painel_gestao', auth='8340'))

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('painel_gestao', auth='8340'))

if __name__ == '__main__':
    app.run(debug=True)