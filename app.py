import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)

# Tenta pegar a URL do banco do Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    # Se existir a URL (estamos no Render), usa Postgres
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    # Se não existir (estamos no seu PC), usa SQLite para não dar erro
    else:
        conn = sqlite3.connect('ponto_local.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Comando compatível com ambos os bancos
    if DATABASE_URL:
        cur.execute('''CREATE TABLE IF NOT EXISTS pontos 
            (id SERIAL PRIMARY KEY, nome TEXT, horario TEXT, tipo TEXT, localizacao TEXT)''')
    else:
        cur.execute('''CREATE TABLE IF NOT EXISTS pontos 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, horario TEXT, tipo TEXT, localizacao TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

with app.app_context():
    init_db()

def obter_horario_sp():
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_sp).strftime('%d/%m/%Y %H:%M:%S')

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
        horario = obter_horario_sp()

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ajuste de sintaxe para cada banco
    sql = 'INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (%s, %s, %s, %s)' if DATABASE_URL else \
          'INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)'
    
    cur.execute(sql, (nome, horario, tipo, loc))
    conn.commit()
    cur.close()
    conn.close()

    if h_manual: return redirect(url_for('painel_gestao', senha='8340'))
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=msg)

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    conn = get_db_connection()
    cur = conn.cursor()
    sql = 'DELETE FROM pontos WHERE id = %s' if DATABASE_URL else 'DELETE FROM pontos WHERE id = ?'
    cur.execute(sql, (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != '8340': return "Acesso Negado", 403
    
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    mes_sel = request.args.get('mes', datetime.now(fuso_sp).strftime('%m'))
    
    conn = get_db_connection()
    if DATABASE_URL:
        cur = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cur = conn.cursor()
        
    cur.execute('SELECT * FROM pontos ORDER BY id DESC')
    pontos_todos = cur.fetchall()
    cur.close()
    conn.close()

    pontos_mes = [p for p in pontos_todos if f"/{mes_sel}/2026" in (p['horario'] if DATABASE_URL else p['horario'])]
    
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

    minutos_esperados = dias_count * 360
    saldo_minutos = minutos_trabalhados - minutos_esperados
    sinal = "+" if saldo_minutos >= 0 else "-"
    abs_min = abs(int(saldo_minutos))
    txt_saldo = f"{sinal}{abs_min // 60}h {abs_min % 60}min"

    meses = [('01','Jan'),('02','Fev'),('03','Mar'),('04','Abr'),('05','Mai'),('06','Jun'),('07','Jul'),('08','Ago'),('09','Set'),('10','Out'),('11','Nov'),('12','Dez')]
    
    return render_template('admin.html', 
                           ultimos_filtrados=pontos_mes, 
                           resumo={'dias': dias_count, 'saldo_texto': txt_saldo}, 
                           meses=meses, 
                           mes_atual=mes_sel)

@app.route('/exportar')
def exportar():
    import pandas as pd
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM pontos", conn)
    conn.close()
    path = 'Relatorio_DraThamiris_Permanente.xlsx'
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    