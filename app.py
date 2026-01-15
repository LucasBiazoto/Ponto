import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('ponto.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    colab = [row['nome'] for row in conn.execute("SELECT nome FROM colaboradoras ORDER BY nome ASC").fetchall()]
    conn.close()
    return render_template('index.html', colaboradoras=colab)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome, tipo = request.form.get('nome'), request.form.get('tipo')
    agora = datetime.now()
    conn = get_db_connection()
    conn.execute("INSERT INTO registros (nome, tipo, horario, data_texto) VALUES (?, ?, ?, ?)", 
                 (nome, tipo, agora.strftime("%d/%m/%Y %H:%M:%S"), agora.strftime("%d/%m/%Y")))
    conn.commit(); conn.close()
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return jsonify({"msg_destaque": msg})

@app.route('/painel_gestao')
def painel_gestao():
    # Se a senha for diferente de 8340, volta para o início
    if request.args.get('senha') != '8340':
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    colabs = conn.execute("SELECT * FROM colaboradoras ORDER BY nome ASC").fetchall()
    relatorio = []
    for c in colabs:
        regs = conn.execute("SELECT tipo, horario FROM registros WHERE nome = ?", (c['nome'],)).fetchall()
        dias = len(set([r['horario'].split(' ')[0] for r in regs]))
        relatorio.append({'id': c['id'], 'nome': c['nome'], 'dias': dias, 'saldo': '0.0h'})
    
    ultimos = conn.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    return render_template('admin.html', relatorio=relatorio, ultimos=ultimos)

@app.route('/cadastrar_colaboradora', methods=['POST'])
def cadastrar():
    nome = request.form.get('nome_novo')
    if nome:
        conn = get_db_connection()
        conn.execute("INSERT INTO colaboradoras (nome) VALUES (?)", (nome,))
        conn.commit(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/excluir_colaboradora/<int:id>')
def excluir_colaboradora(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM colaboradoras WHERE id = ?", (id,))
    conn.commit(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

if __name__ == '__main__':
    app.run(debug=True)