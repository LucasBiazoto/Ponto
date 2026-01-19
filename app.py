import os
import sqlite3
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)
# Nome do banco atualizado para 2026
DATABASE = 'ponto_dra_thamiris_2026.db'

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

def obter_horario_sp():
    """Retorna o horário atual no fuso de São Paulo"""
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

    # Se for lançamento manual pela gestão
    if h_manual:
        dt = datetime.strptime(h_manual, '%Y-%m-%dT%H:%M')
        horario = dt.strftime('%d/%m/%Y %H:%M:%S')
        loc = "Lançamento Manual"
    else:
        # Ponto real batido pela funcionária
        horario = obter_horario_sp()

    conn = get_db_connection()
    conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                 (nome, horario, tipo, loc))
    conn.commit()
    conn.close()

    if h_manual:
        return redirect(url_for('painel_gestao', senha='8340'))
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=msg)

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    # A exclusão redireciona de volta para a gestão com a senha
    conn = get_db_connection()
    conn.execute('DELETE FROM pontos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/painel_gestao')
def painel_gestao():
    # Segurança obrigatória por senha
    if request.args.get('senha') != '8340':
        return "<h1>Acesso Negado</h1>", 403
    
    # Define o mês atual como padrão se nenhum for selecionado
    fuso_sp = pytz.timezone('America/Sao_Paulo')
    mes_atual_sistema = datetime.now(fuso_sp).strftime('%m')
    mes_sel = request.args.get('mes', mes_atual_sistema)
    
    conn = get_db_connection()
    pontos_todos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()

    # FILTRAGEM: Pega apenas os pontos do mês selecionado de 2026
    pontos_mes = [p for p in pontos_todos if f"/{mes_sel}/2026" in p['horario']]
    
    # LÓGICA DE CÁLCULO DE BANCO DE HORAS
    registro_dia = {}
    for p in reversed(pontos_mes):
        data = p['horario'].split()[0]
        hora_dt = datetime.strptime(p['horario'], '%d/%m/%Y %H:%M:%S')
        if data not in registro_dia:
            registro_dia[data] = {'E': None, 'S': None}
        
        # Considera a primeira entrada e a última saída do dia
        if p['tipo'] == 'Entrada' and not registro_dia[data]['E']:
            registro_dia[data]['E'] = hora_dt
        elif p['tipo'] == 'Saída':
            registro_dia[data]['S'] = hora_dt

    total_minutos_trabalhados = 0
    dias_count = 0
    
    for d, h in registro_dia.items():
        if h['E'] and h['S']:
            # Diferença em minutos entre entrada e saída
            duracao = (h['S'] - h['E']).total_seconds() / 60
            total_minutos_trabalhados += duracao
            dias_count += 1

    # SALDO: (Trabalhado) - (Dias trabalhados * 360 minutos da jornada de 6h)
    minutos_esperados = dias_count * 360
    saldo_minutos = total_minutos_trabalhados - minutos_esperados
    
    # Formatação visual do saldo (+ ou -)
    sinal = "+" if saldo_minutos >= 0 else "-"
    abs_min = abs(int(saldo_minutos))
    txt_saldo = f"{sinal}{abs_min // 60}h {abs_min % 60}min"

    meses_lista = [
        ('01','Janeiro'),('02','Fevereiro'),('03','Março'),('04','Abril'),
        ('05','Maio'),('06','Junho'),('07','Julho'),('08','Agosto'),
        ('09','Setembro'),('10','Outubro'),('11','Novembro'),('12','Dezembro')
    ]
    
    return render_template('admin.html', 
                           ultimos_filtrados=pontos_mes, 
                           resumo={'dias': dias_count, 'saldo_texto': txt_saldo, 'saldo_minutos': saldo_minutos}, 
                           meses=meses_lista, 
                           mes_atual=mes_sel)

@app.route('/backup')
def backup():
    return send_file(DATABASE, as_attachment=True)

@app.route('/exportar')
def exportar():
    import pandas as pd
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM pontos", conn)
    conn.close()
    path = 'Relatorio_DraThamiris_2026.xlsx'
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    # Configuração para rodar no Render ou Local
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)