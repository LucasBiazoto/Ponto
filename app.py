import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
DATABASE = 'ponto_v2.db' 

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS colaboradores (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL)')
    conn.execute('CREATE TABLE IF NOT EXISTS pontos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, horario TEXT NOT NULL, tipo TEXT NOT NULL, localizacao TEXT)')
    # Fixa Esther Julia
    conn.execute("INSERT OR IGNORE INTO colaboradores (id, nome) VALUES (1, 'Esther Julia')")
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    colaboradores = conn.execute('SELECT * FROM colaboradores').fetchall()
    conn.close()
    return render_template('index.html', colaboradores=colaboradores)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('nome')
    tipo = request.form.get('tipo')
    # Se vier do formulário manual, usa o horário digitado, senão usa o atual
    horario_manual = request.form.get('horario_manual')
    
    if horario_manual:
        try:
            dt = datetime.strptime(horario_manual, '%Y-%m-%dT%H:%M')
            horario = dt.strftime('%d/%m/%Y %H:%M:%S')
            loc = "Lançamento Manual"
        except:
            horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            loc = "Erro no formato manual"
    else:
        horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        loc = request.form.get('localizacao', 'Não informada')

    conn = get_db_connection()
    conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                 (nome, horario, tipo, loc))
    conn.commit()
    conn.close()
    
    if horario_manual:
        return redirect(url_for('painel_gestao', senha='8340'))
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=msg)

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != '8340': return "Acesso Negado", 403
    
    conn = get_db_connection()
    colaboradores = conn.execute('SELECT * FROM colaboradores').fetchall()
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', relatorio=[], ultimos=pontos[:10], colaboradores=colaboradores)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)