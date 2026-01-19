import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
DATABASE = 'ponto_estetica_final.db'

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
    if not pontos_filtrados:
        return 0, "+0h 0min"
    # Conta dias único formatando a string de data (DD/MM/YYYY)
    dias = len(set(p['horario'].split()[0] for p in pontos_filtrados))
    # Exemplo: Jornada de 6h (360 min). Ajuste conforme a necessidade real.
    total_minutos = dias * 360 
    horas = total_minutos // 60
    minutos = total_minutos % 60
    return dias, f"+{horas}h {minutos}min"

@app.route('/')
def index():
    return render_template('index.html', colaboradores=[{'nome': 'Esther Julia'}])

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    try:
        nome = request.form.get('nome')
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

        if h_manual:
            return redirect(url_for('painel_gestao', senha='8340'))
        
        msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
        return f"<h1>{msg}</h1><script>setTimeout(()=>window.location.href='/', 3000)</script>"
    except Exception as e:
        return f"Erro crítico: {e}", 500

@app.route('/painel_gestao')
def painel_gestao():
    # Segurança por senha restaurada
    if request.args.get('senha') != '8340':
        return "Acesso Negado", 403
    
    mes_filtro = request.args.get('mes')
    conn = get_db_connection()
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()

    if mes_filtro:
        pontos = [p for p in pontos if f"/{mes_filtro}/" in p['horario']]

    dias, saldo = calcular_estatisticas(pontos)
    meses = ['01','02','03','04','05','06','07','08','09','10','11','12']
    
    return render_template('admin.html', ultimos=pontos, 
                           colaboradores=[{'nome': 'Esther Julia', 'dias': dias, 'saldo': saldo}], 
                           meses=meses)

@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM pontos", conn)
    conn.close()
    df.to_excel('Relatorio_DraThamiris.xlsx', index=False)
    return send_file('Relatorio_DraThamiris.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))