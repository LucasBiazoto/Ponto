import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import pytz
import io
import json

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# CONEXÃO COM O BANCO DE DADOS
def get_db_connection():
    # O Vercel injeta a URL do banco automaticamente aqui
    conn = psycopg2.connect(os.environ.get('POSTGRES_URL'))
    return conn

# CRIA A TABELA E AS COLUNAS NECESSÁRIAS
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id SERIAL PRIMARY KEY,
            tipo TEXT,
            data TEXT,
            mes TEXT,
            hora TEXT,
            geo TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), f"{lat}, {lon}"))
    conn.commit()
    cur.close()
    conn.close()
    
    flash("Bom trabalho meu bem 🌸" if tipo == 'Entrada' else "Bom descanso meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT tipo, data, hora, id FROM pontos WHERE mes = %s ORDER BY id DESC', (mes_f,))
    registros = cur.fetchall()
    cur.close()
    conn.close()

    diario = {}
    for tipo, data, hora, p_id in registros:
        if data not in diario: diario[data] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if tipo == 'Entrada': diario[data]['e'] = hora; diario[data]['id_e'] = p_id
        else: diario[data]['s'] = hora; diario[data]['id_s'] = p_id

    tabela = []
    for data, v in diario.items():
        # Lógica simples de saldo (exemplo 6h)
        tabela.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': '#d68c9a', 'saldo': '--:--'})

    return render_template('gestao.html', registros=tabela, mes_atual=mes_f)

# --- NOVAS FUNÇÕES ADICIONADAS PARA O PAINEL FUNCIONAR 100% ---

@app.route('/ponto_manual', methods=['POST'])
def ponto_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_m = request.form.get('data') # AAAA-MM-DD
    hora_m = request.form.get('hora')
    tipo_m = request.form.get('tipo')
    
    data_f = datetime.strptime(data_m, '%Y-%m-%d').strftime('%d/%m/%Y')
    mes_f = data_m.split('-')[1]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo_m, data_f, mes_f, hora_m, "Manual"))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if not session.get('admin_logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/exportar_backup')
def exportar_backup():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM pontos')
    dados = cur.fetchall()
    cur.close()
    conn.close()
    output = json.dumps(dados, indent=4)
    return send_file(io.BytesIO(output.encode()), mimetype='application/json', as_attachment=True, download_name='backup_clinica.json')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == "8340":
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))