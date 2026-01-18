import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
DATABASE = 'ponto_estetica_v6.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT NOT NULL, 
            horario TEXT NOT NULL, 
            tipo TEXT NOT NULL, 
            localizacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

def calcular_estatisticas(pontos_filtrados):
    # Base de 6h diárias (360 minutos)
    dias_trabalhados = len(set(p['horario'].split()[0] for p in pontos_filtrados))
    # Cálculo de horas extras (Exemplo: saldo acumulado positivo)
    minutos_totais = dias_trabalhados * 360 
    horas = minutos_totais // 60
    minutos = minutos_totais % 60
    return dias_trabalhados, f"+{horas}h {minutos}min"

@app.route('/')
def index():
    colaboradoras = [{'nome': 'Esther Julia'}]
    return render_template('index.html', colaboradores=colaboradoras)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    try:
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')
        horario_manual = request.form.get('horario_manual')
        localizacao = request.form.get('localizacao', 'Não informada')
        
        if horario_manual:
            dt = datetime.strptime(horario_manual, '%Y-%m-%dT%H:%M')
            horario = dt.strftime('%d/%m/%Y %H:%M:%S')
            localizacao = "Lançamento Manual"
        else:
            horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        conn = get_db_connection()
        conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                     (nome, horario, tipo, localizacao))
        conn.commit()
        conn.close()
        
        if horario_manual:
            return redirect(url_for('painel_gestao', senha='8340'))
        
        # RESTAURADO: Mensagens personalizadas
        msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
        return render_template('sucesso.html', mensagem=msg)
    except Exception as e:
        return f"Erro ao registrar: {e}", 500

@app.route('/painel_gestao')
def painel_gestao():
    # RESTAURADO: Bloqueio por senha
    senha = request.args.get('senha')
    if senha != '8340': 
        return "<h1>Acesso Negado</h1><p>Use a senha correta na URL.</p>", 403
    
    mes_filtro = request.args.get('mes')
    conn = get_db_connection()
    query = 'SELECT * FROM pontos ORDER BY id DESC'
    pontos = conn.execute(query).fetchall()
    conn.close()
    
    # Filtro simplificado por mês
    if mes_filtro:
        pontos = [p for p in pontos if f"/{mes_filtro}/" in p['horario']]

    dias, saldo = calcular_estatisticas(pontos)
    colaboradoras = [{'nome': 'Esther Julia', 'dias': dias, 'saldo': saldo}]
    meses = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
    
    return render_template('admin.html', ultimos=pontos, colaboradores=colaboradoras, meses=meses)

@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM pontos", conn)
    conn.close()
    df.to_excel('Relatorio_DraThamiris.xlsx', index=False)
    return send_file('Relatorio_DraThamiris.xlsx', as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)