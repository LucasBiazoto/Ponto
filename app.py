import sqlite3
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('ponto.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS registros (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, tipo TEXT, horario TEXT, data_texto TEXT, localizacao TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS colaboradoras (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)')
    conn.commit()
    conn.close()

def calcular_jornada(entrada_str, saida_str):
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            inicio = datetime.strptime(entrada_str, formato)
            fim = datetime.strptime(saida_str, formato)
            horas = (fim - inicio).total_seconds() / 3600
            return round(horas, 2), round(horas - 6.0, 2)
        except: continue
    return 0, 0

@app.route('/')
def index():
    conn = get_db_connection()
    colab = [row['nome'] for row in conn.execute("SELECT nome FROM colaboradoras ORDER BY nome ASC").fetchall()]
    conn.close()
    return render_template('index.html', colaboradoras=colab)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome, tipo, lat, lon = request.form.get('nome'), request.form.get('tipo'), request.form.get('lat'), request.form.get('lon')
    status_local = "✅ Na Clínica"
    if lat and lon:
        dist = ((float(lat) - (-23.5255))**2 + (float(lon) - (-46.5273))**2)**0.5
        if dist > 0.002: status_local = "📍 Fora da Clínica"
    agora = datetime.now()
    conn = get_db_connection()
    conn.execute("INSERT INTO registros (nome, tipo, horario, data_texto, localizacao) VALUES (?, ?, ?, ?, ?)", 
                 (nome, tipo, agora.strftime("%d/%m/%Y %H:%M:%S"), agora.strftime("%d/%m/%Y"), status_local))
    conn.commit(); conn.close()
    # Mensagens personalizadas conforme solicitado
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return jsonify({"msg_destaque": msg, "msg_sub": status_local})

@app.route('/painel_gestao')
def painel_gestao():
    # Sistema de senha simples e direto
    if request.args.get('senha') != '8340':
        return render_template('login_admin.html'), 403
    
    conn = get_db_connection()
    colabs = conn.execute("SELECT * FROM colaboradoras ORDER BY nome ASC").fetchall()
    relatorio = []
    for c in colabs:
        regs = conn.execute("SELECT tipo, horario FROM registros WHERE nome = ?", (c['nome'],)).fetchall()
        datas = sorted(list(set([r['horario'].split(' ')[0] for r in regs])))
        saldo_t = 0.0
        for d in datas:
            e = [r['horario'] for r in regs if r['horario'].startswith(d) and r['tipo'] == 'Entrada']
            s = [r['horario'] for r in regs if r['horario'].startswith(d) and r['tipo'] == 'Saída']
            if e and s:
                _, saldo = calcular_jornada(e[0], s[-1])
                saldo_t += saldo
        relatorio.append({'id': c['id'], 'nome': c['nome'], 'dias': len(datas), 'saldo': round(saldo_t, 2)})
    
    ultimos = conn.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 15").fetchall()
    conn.close()
    return render_template('admin.html', relatorio=relatorio, ultimos=ultimos)

@app.route('/cadastrar_colaboradora', methods=['POST'])
def cadastrar():
    nome = request.form.get('nome_novo')
    if nome:
        conn = get_db_connection()
        try: conn.execute("INSERT INTO colaboradoras (nome) VALUES (?)", (nome,)); conn.commit()
        except: pass
        conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/excluir_colaboradora/<int:id>')
def excluir_colaboradora(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM colaboradoras WHERE id = ?", (id,))
    conn.commit(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT nome, tipo, horario, localizacao FROM registros", conn)
    conn.close()
    df.to_excel("Relatorio_Estetica.xlsx", index=False)
    return send_file("Relatorio_Estetica.xlsx", as_attachment=True)

init_db()
if __name__ == '__main__':
    app.run(debug=True)