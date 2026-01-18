import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
DATABASE = 'ponto_dra_thamiris.db' 

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Criamos apenas a tabela de registros de ponto
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

@app.route('/')
def index():
    # FIXO NO CÓDIGO: Isso garante que ela apareça na tela inicial sem erros
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
    
    if horario_manual:
        return redirect(url_for('painel_gestao', senha='8340'))
    
    # Mensagens personalizadas para Dra Thamiris Araujo
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=msg)

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != '8340': return "Acesso Negado", 403
    
    conn = get_db_connection()
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    conn.close()
    
    colaboradoras = [{'nome': 'Esther Julia'}]
    return render_template('admin.html', relatorio=[], ultimos=pontos[:20], colaboradores=colaboradoras)

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