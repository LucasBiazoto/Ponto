import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)

# CONEXÃO COM BANCO PERMANENTE
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    # Se estiver no Render, usa o banco permanente. Se estiver no PC, dá erro avisando.
    if not DATABASE_URL:
        raise ValueError("A variável DATABASE_URL não foi encontrada!")
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Cria a tabela no banco permanente se não existir
    cur.execute('''CREATE TABLE IF NOT EXISTS pontos 
        (id SERIAL PRIMARY KEY, nome TEXT, horario TEXT, tipo TEXT, localizacao TEXT)''')
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
    # Sintaxe específica para Postgres (%s)
    cur.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (%s, %s, %s, %s)',
                 (nome, horario, tipo, loc))
    conn.commit()
    cur.close()
    conn.close()

    if h_manual:
        return redirect(url_for('painel_gestao', senha='8340'))
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=msg)

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != '8340':
        return "<h1>Acesso Negado</h1>", 403
    
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    mes_sel = request.args.get('mes', datetime.now(fuso_sp).strftime('%m'))
    
    conn = get_db_connection()
    # RealDictCursor faz o Postgres se comportar como o dicionário que o HTML espera
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM pontos ORDER BY id DESC')
    pontos_todos = cur.fetchall()
    cur.close()
    conn.close()

    pontos_mes = [p for p in pontos_todos if f"/{mes_sel}/2026" in p['horario']]
    
    registro_dia = {}
    for p in reversed(pontos_mes):
        data = p['horario'].split()[0]
        hora_dt = datetime.strptime(p['horario'], '%d/%m/%Y %H:%M:%S')
        if data not in registro_dia:
            registro_dia[data] = {'E': None, 'S': None}
        if p['tipo'] == 'Entrada' and not registro_dia[data]['E']:
            registro_dia[data]['E'] = hora_dt
        elif p['tipo'] == 'Saída':
            registro_dia[data]['S'] = hora_dt

    total_minutos = 0
    dias_count = 0
    for d, h in registro_dia.items():
        if h['E'] and h['S']:
            total_minutos += (h['S'] - h['E']).total_seconds() / 60
            dias_count += 1

    minutos_esperados = dias_count * 360
    saldo = total_minutos - minutos_esperados
    sinal = "+" if saldo >= 0 else "-"
    abs_min = abs(int(saldo))
    txt_saldo = f"{sinal}{abs_min // 60}h {abs_min % 60}min"

    meses_lista = [('01','Janeiro'),('02','Fevereiro'),('03','Março'),('04','Abril'),('05','Maio'),('06','Junho'),('07','Julho'),('08','Agosto'),('09','Setembro'),('10','Outubro'),('11','Novembro'),('12','Dezembro')]
    
    return render_template('admin.html', ultimos_filtrados=pontos_mes, resumo={'dias': dias_count, 'saldo_texto': txt_saldo}, meses=meses_lista, mes_atual=mes_sel)

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