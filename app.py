import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import pandas as pd

app = Flask(__name__)
app.secret_key = "thamiris_secret"
DATABASE = 'ponto_estetica_2026.db'

# Coordenadas Spot Offices Penha (Exemplo aproximado para validação)
EMPRESA_LAT, EMPRESA_LON = -23.5234, -46.5442 

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()

    # Filtrar pontos do mês atual/selecionado para cálculo
    pontos_mes = [p for p in pontos if f"/{mes_sel}/2026" in p['horario']]
    
    # Lógica de Cálculo de Horas (Base 6h)
    logica_ponto = {}
    for p in reversed(pontos_mes):
        data = p['horario'].split()[0]
        hora = datetime.strptime(p['horario'], '%d/%m/%Y %H:%M:%S')
        if data not in logica_ponto: logica_ponto[data] = {'E': None, 'S': None}
        if p['tipo'] == 'Entrada' and not logica_ponto[data]['E']: logica_ponto[data]['E'] = hora
        elif p['tipo'] == 'Saída': logica_ponto[data]['S'] = hora

    total_minutos_trabalhados = 0
    dias_count = 0
    for data, horas in logica_ponto.items():
        if horas['E'] and horas['S']:
            diff = (horas['S'] - horas['E']).total_seconds() / 60
            total_minutos_trabalhados += diff
            dias_count += 1

    # Saldo: Minutos trabalhados - (Dias * 360 minutos da jornada de 6h)
    minutos_devidos = dias_count * 360
    saldo_total_minutos = total_minutos_trabalhados - minutos_devidos
    
    horas_saldo = int(abs(saldo_total_minutos) // 60)
    min_saldo = int(abs(saldo_total_minutos) % 60)
    sinal = "+" if saldo_total_minutos >= 0 else "-"
    txt_saldo = f"{sinal}{horas_saldo}h {min_saldo}min"

    meses_lista = [('01', 'Janeiro'), ('02', 'Fevereiro'), ('03', 'Março'), ('04', 'Abril'), ('05', 'Maio'), ('06', 'Junho'), ('07', 'Julho'), ('08', 'Agosto'), ('09', 'Setembro'), ('10', 'Outubro'), ('11', 'Novembro'), ('12', 'Dezembro')]
    
    return render_template('admin.html', ultimos=pontos, resumo={'dias': dias_count, 'saldo': txt_saldo}, meses=meses_lista, mes_atual=mes_sel)

@app.route('/backup')
def backup():
    return send_file(DATABASE, as_attachment=True)