import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd

app = Flask(__name__)
# Nome exato do arquivo que aparece no seu VS Code
DATABASE = 'ponto.db' 

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Criação das tabelas com nomes corretos
    conn.execute('''CREATE TABLE IF NOT EXISTS colaboradores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS pontos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        horario TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        localizacao TEXT)''')
    
    # Remove nomes de teste e fixa Esther Julia definitivamente
    conn.execute("DELETE FROM colaboradores WHERE nome = 'Lucas Moreira Biazoto'")
    conn.execute("INSERT OR IGNORE INTO colaboradores (id, nome) VALUES (1, 'Esther Julia')")
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    colaboradores = conn.execute('SELECT * FROM colaboradores').fetchall()
    conn.close()
    return render_template('index.html', colaboradores=colaboradores)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form['nome']
    tipo = request.form['tipo']
    localizacao = request.form.get('localizacao', 'Não informada')
    horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                 (nome, horario, tipo, localizacao))
    conn.commit()
    conn.close()
    
    mensagem = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return render_template('sucesso.html', mensagem=mensagem)

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != '8340':
        return "Acesso Negado", 403
    
    mes_filtro = request.args.get('mes', datetime.now().strftime('%m'))
    ano_filtro = request.args.get('ano', datetime.now().strftime('%Y'))
    
    conn = get_db_connection()
    colaboradores = conn.execute('SELECT * FROM colaboradores').fetchall()
    # CORREÇÃO: Busca na tabela 'pontos' (não registros)
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    
    relatorio = []
    for colab in colaboradores:
        pontos_colab = [p for p in pontos if p['nome'] == colab['nome'] and p['horario'][3:10] == f"{mes_filtro}/{ano_filtro}"]
        
        total_segundos = 0
        dias_trabalhados = set()
        
        # Lógica de cálculo de horas (Carga 6h)
        for i in range(0, len(pontos_colab)-1, 2):
            if pontos_colab[i]['tipo'] == 'Entrada' and pontos_colab[i+1]['tipo'] == 'Saída':
                fmt = '%d/%m/%Y %H:%M:%S'
                try:
                    e = datetime.strptime(pontos_colab[i]['horario'], fmt)
                    s = datetime.strptime(pontos_colab[i+1]['horario'], fmt)
                    total_segundos += (s - e).total_seconds()
                    dias_trabalhados.add(pontos_colab[i]['horario'][:10])
                except:
                    continue
        
        horas_devidas = len(dias_trabalhados) * 6 * 3600
        saldo_segundos = total_segundos - horas_devidas
        
        sinal = "-" if saldo_segundos < 0 else "+"
        abs_saldo = abs(int(saldo_segundos))
        h = abs_saldo // 3600
        m = (abs_saldo % 3600) // 60
        
        relatorio.append({
            'id': colab['id'],
            'nome': colab['nome'],
            'dias': len(dias_trabalhados),
            'saldo_formatado': f"{sinal}{h}h {m}min"
        })
        
    conn.close()
    return render_template('admin.html', relatorio=relatorio, ultimos=pontos[:10])

@app.route('/backup')
def backup():
    return send_file(DATABASE, as_attachment=True)

@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    # CORREÇÃO: Nome da tabela unificado para 'pontos'
    df = pd.read_sql_query("SELECT * FROM pontos", conn)
    conn.close()
    df.to_excel('Relatorio_Pontos.xlsx', index=False)
    return send_file('Relatorio_Pontos.xlsx', as_attachment=True)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)