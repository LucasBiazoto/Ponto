import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)
DATABASE = 'ponto_estetica_2026.db'

# Coordenadas aproximadas do Spot Offices Penha para conferência no painel
LAT_CLINICA, LON_CLINICA = -23.523, -46.544 

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS pontos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, horario TEXT, tipo TEXT, localizacao TEXT)''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/')
def index():
    return render_template('index.html', colaboradores=[{'nome': 'Esther Julia'}])

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = "Esther Julia"
    tipo = request.form.get('tipo')
    loc = request.form.get('localizacao', 'Não informada')
    h_manual = request.form.get('horario_manual')

    if h_manual:
        dt = datetime.strptime(h_manual, '%Y-%m-%dT%H:%M')
        horario = dt.strftime('%d/%m/%Y %H:%M:%S')
        loc = "Lançamento Manual"
    else:
        horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    conn = get_db_connection()
    conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                 (nome, horario, tipo, loc))
    conn.commit()
    conn.close()

    if h_manual: return redirect(url_for('painel_gestao', senha='8340'))
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=msg)

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM pontos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != '8340': return "Acesso Negado", 403
    
    mes_sel = request.args.get('mes', datetime.now().strftime('%m'))
    conn = get_db_connection()
    pontos_todos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()

    pontos_mes = [p for p in pontos_todos if f"/{mes_sel}/2026" in p['horario']]
    
    # Lógica de Cálculo de Horas (Base 6h diárias)
    registro_dia = {}
    for p in reversed(pontos_mes):
        data = p['horario'].split()[0]
        hora_dt = datetime.strptime(p['horario'], '%d/%m/%Y %H:%M:%S')
        if data not in registro_dia: registro_dia[data] = {'E': None, 'S': None}
        if p['tipo'] == 'Entrada' and not registro_dia[data]['E']: registro_dia[data]['E'] = hora_dt
        elif p['tipo'] == 'Saída': registro_dia[data]['S'] = hora_dt

    minutos_trabalhados = 0
    dias_count = 0
    for d, h in registro_dia.items():
        if h['E'] and h['S']:
            minutos_trabalhados += (h['S'] - h['E']).total_seconds() / 60
            dias_count += 1

    saldo_minutos = minutos_trabalhados - (dias_count * 360) # 360 min = 6h
    sinal = "+" if saldo_minutos >= 0 else "-"
    abs_min = abs(int(saldo_minutos))
    txt_saldo = f"{sinal}{abs_min // 60}h {abs_min % 60}min"

    meses = [('01','Jan'),('02','Fev'),('03','Mar'),('04','Abr'),('05','Mai'),('06','Jun'),('07','Jul'),('08','Ago'),('09','Set'),('10','Out'),('11','Nov'),('12','Dez')]
    return render_template('admin.html', ultimos=pontos_todos, resumo={'dias': dias_count, 'saldo': txt_saldo}, meses=meses, mes_atual=mes_sel)

@app.route('/backup')
def backup():
    return send_file(DATABASE, as_attachment=True)