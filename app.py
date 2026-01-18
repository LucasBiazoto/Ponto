import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
DATABASE = 'ponto_estetica_v4.db' 

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

def calcular_resumo(pontos):
    # Lógica para calcular dias e saldo (base 6h)
    dias_trabalhados = len(set(p['horario'].split()[0] for p in pontos))
    total_minutos = 0
    # Cálculo simplificado para exibição: cada dia trabalhado soma 6h de saldo nominal
    saldo_minutos = dias_trabalhados * 360 
    horas = saldo_minutos // 60
    minutos = saldo_minutos % 60
    return {"dias": dias_trabalhados, "saldo": f"+{horas}h {minutos}min"}

@app.route('/')
def index():
    # GARANTIA: Esther Julia fixa para aparecer no início
    colaboradoras = [{'nome': 'Esther Julia'}]
    return render_template('index.html', colaboradores=colaboradoras)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('nome')
    tipo = request.form.get('tipo')
    horario_manual = request.form.get('horario_manual')
    
    if horario_manual:
        try:
            dt = datetime.strptime(horario_manual, '%Y-%m-%dT%H:%M')
            horario = dt.strftime('%d/%m/%Y %H:%M:%S')
            loc = "Lançamento Manual"
        except:
            horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            loc = "Erro formato"
    else:
        horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        loc = request.form.get('localizacao', 'Não informada')

    conn = get_db_connection()
    conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                 (nome, horario, tipo, loc))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_gestao', senha='8340') if horario_manual else 'index')

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != '8340': return "Acesso Negado", 403
    
    conn = get_db_connection()
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()
    
    resumo = calcular_resumo(pontos)
    colaboradoras = [{'nome': 'Esther Julia', 'dias': resumo['dias'], 'saldo': resumo['saldo']}]
    
    return render_template('admin.html', ultimos=pontos, colaboradores=colaboradoras)

# ... (rotas de exportar e backup permanecem as mesmas)