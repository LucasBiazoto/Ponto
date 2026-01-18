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
    conn.execute('''CREATE TABLE IF NOT EXISTS colaboradores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS pontos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        horario TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        localizacao TEXT)''')
    
    # Garante Esther Julia como única funcionária fixa
    conn.execute("DELETE FROM colaboradores WHERE nome = 'Lucas Moreira Biazoto'")
    conn.execute("INSERT OR IGNORE INTO colaboradores (id, nome) VALUES (1, 'Esther Julia')")
    
    conn.commit()
    conn.close()

# Inicializa o banco ao rodar o app
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
    nome = request.form['nome']
    tipo = request.form['tipo']
    localizacao = request.form.get('localizacao', 'Manual/Não informada')
    
    # Se vier do formulário manual, usa o horário digitado, senão usa o atual
    horario_form = request.form.get('horario_manual')
    if horario_form:
        try:
            # Converte de YYYY-MM-DDTHH:MM para DD/MM/YYYY HH:MM:SS
            dt = datetime.strptime(horario_form, '%Y-%m-%dT%H:%M')
            horario = dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    else:
        horario = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO pontos (nome, horario, tipo, localizacao) VALUES (?, ?, ?, ?)',
                 (nome, horario, tipo, localizacao))
    conn.commit()
    conn.close()
    
    # Se for manual, volta para o painel, se for batida normal, vai para sucesso
    if horario_form:
        return redirect(url_for('painel_gestao', senha='8340'))
    
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
    pontos = conn.execute('SELECT * FROM pontos ORDER BY id DESC').fetchall()
    
    relatorio = []
    for colab in colaboradores:
        pontos_colab = [p for p in pontos if p['nome'] == colab['nome'] and p['horario'][3:10] == f"{mes_filtro}/{ano_filtro}"]
        # Inverte para cálculo cronológico
        pontos_calc = pontos_colab[::-1]
        
        total_segundos = 0
        dias_trabalhados = set()
        
        for i in range(0, len(pontos_calc)-1, 2):
            if pontos_calc[i]['tipo'] == 'Entrada' and pontos_calc[i+1]['tipo'] == 'Saída':
                try:
                    fmt = '%d/%m/%Y %H:%M:%S'
                    e = datetime.strptime(pontos_calc[i]['horario'], fmt)
                    s = datetime.strptime(pontos_calc[i+1]['horario'], fmt)
                    total_segundos += (s - e).total_seconds()
                    dias_trabalhados.add(pontos_calc[i]['horario'][:10])
                except: continue
        
        abs_saldo = abs(int(total_segundos - (len(dias_trabalhados) * 6 * 3600)))
        sinal = "-" if (total_segundos - (len(dias_trabalhados) * 6 * 3600)) < 0 else "+"
        
        relatorio.append({
            'nome': colab['nome'],
            'dias': len(dias_trabalhados),
            'saldo_formatado': f"{sinal}{abs_saldo // 3600}h {(abs_saldo % 3600) // 60}min"
        })
    conn.close()
    return render_template('admin.html', relatorio=relatorio, ultimos=pontos[:15], colaboradores=colaboradores)

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