import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
DATABASE = 'ponto_dra_thamiris_v7.db'

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
    return render_template('sucesso.html', mensagem=msg)

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != '8340':
        return "Acesso Negado", 403
    
    mes_selecionado = request.args.get('mes', '')
    conn = get_db_connection()
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()

    if mes_selecionado:
        pontos = [p for p in pontos if f"/{mes_selecionado}/" in p['horario']]

    # Cálculo de dias e saldo
    dias = len(set(p['horario'].split()[0] for p in pontos))
    saldo = f"+{dias * 6}h 0min" # Base 6h por dia
    
    meses = [f"{i:02d}" for i in range(1, 13)]
    return render_template('admin.html', ultimos=pontos, 
                           colaboradores=[{'nome': 'Esther Julia', 'dias': dias, 'saldo': saldo}], 
                           meses=meses)