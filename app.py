import sqlite3
import pandas as pd
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify

app = Flask(__name__)
app.secret_key = 'dra_thamiris_luxury_final_revisado'

# Função para conectar ao banco de dados com tratamento de caminho
def get_db_connection():
    # No Render, o SQLite funciona bem na raiz do projeto
    conn = sqlite3.connect('ponto.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Tabela de Registros de Ponto
    cursor.execute('''CREATE TABLE IF NOT EXISTS registros 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome TEXT, 
                       tipo TEXT, 
                       horario TEXT, 
                       data_texto TEXT, 
                       localizacao TEXT)''')
    # Tabela de Colaboradoras
    cursor.execute('''CREATE TABLE IF NOT EXISTS colaboradoras 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

def calcular_jornada(entrada_str, saida_str):
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            inicio = datetime.strptime(entrada_str, formato)
            fim = datetime.strptime(saida_str, formato)
            diff = fim - inicio
            horas = diff.total_seconds() / 3600
            return round(horas, 2), round(horas - 6.0, 2)
        except: continue
    return 0, 0

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM colaboradoras ORDER BY nome ASC")
    colab = [row['nome'] for row in cursor.fetchall()]
    conn.close()
    return render_template('index.html', colaboradoras=colab)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('nome')
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    
    # Localização da Clínica (Ajuste se necessário)
    CLINICA_LAT, CLINICA_LON = -23.5255, -46.5273
    status_local = "✅ OK"
    fora = False
    
    if lat and lon:
        distancia = ((float(lat) - CLINICA_LAT)**2 + (float(lon) - CLINICA_LON)**2)**0.5
        if distancia > 0.002: 
            status_local = "📍 Fora da Clínica"
            fora = True
    else: 
        status_local = "❓ Sem GPS"

    agora = datetime.now()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registros (nome, tipo, horario, data_texto, localizacao) VALUES (?, ?, ?, ?, ?)", 
                   (nome, tipo, agora.strftime("%d/%m/%Y %H:%M:%S"), agora.strftime("%d/%m/%Y"), status_local))
    conn.commit()
    conn.close()
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return jsonify({"status": "SUCESSO", "msg_destaque": msg, "msg_sub": f"Local: {status_local}", "fora": fora})

@app.route('/painel_gestao')
def painel_gestao():
    mes = request.args.get('mes', datetime.now().strftime("%m"))
    ano = datetime.now().strftime('%Y')
    filtro = f"/{mes}/{ano}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM colaboradoras ORDER BY nome ASC")
    colab_lista = cursor.fetchall()
    
    relatorio = []
    presentes = []
    total_extras_mes = 0.0
    
    for c in colab_lista:
        n = c['nome']
        cursor.execute("SELECT tipo, horario FROM registros WHERE nome = ? AND horario LIKE ?", (n, f"%{filtro}%"))
        regs = cursor.fetchall()
        
        # Verificar quem está presente hoje
        if regs and regs[-1]['tipo'] == 'Entrada' and regs[-1]['horario'].startswith(datetime.now().strftime("%d/%m/%Y")):
            presentes.append(n)
            
        datas = sorted(list(set([r['horario'].split(' ')[0] for r in regs])))
        total_saldo = 0.0
        dias = 0
        for d in datas:
            e = [r['horario'] for r in regs if r['horario'].startswith(d) and r['tipo'] == 'Entrada']
            s = [r['horario'] for r in regs if r['horario'].startswith(d) and r['tipo'] == 'Saída']
            if e and s:
                dias += 1
                _, saldo = calcular_jornada(e[0], s[-1])
                total_saldo += saldo
        
        total_extras_mes += total_saldo
        relatorio.append({'nome': n, 'dias': dias, 'saldo': round(total_saldo, 2)})
    
    cursor.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 50")
    ultimos = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', relatorio=relatorio, ultimos=ultimos, colaboradoras=colab_lista, mes_sel=mes, presentes=presentes, total_extras=round(total_extras_mes, 1))

@app.route('/cadastrar_colaboradora', methods=['POST'])
def cadastrar():
    nome = request.form.get('nome_novo').strip()
    if nome:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO colaboradoras (nome) VALUES (?)", (nome,))
            conn.commit()
        except: pass
        conn.close()
    return redirect(url_for('painel_gestao'))

@app.route('/lancar_manual', methods=['POST'])
def lancar_manual():
    n = request.form.get('nome')
    t = request.form.get('tipo')
    dt = request.form.get('data_hora').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registros (nome, tipo, horario, data_texto, localizacao) VALUES (?, ?, ?, ?, ?)", 
                   (n, t, dt, dt.split(' ')[0], "📝 Manual (OK)"))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_gestao'))

@app.route('/exportar')
def exportar():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT nome, tipo, horario, localizacao FROM registros", conn)
    conn.close()
    caminho_arquivo = "Relatorio_Estetica.xlsx"
    df.to_excel(caminho_arquivo, index=False)
    return send_file(caminho_arquivo, as_attachment=True)

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_gestao'))

# Inicialização crucial para o Render
init_db()

if __name__ == '__main__':
    # Rodar localmente
    app.run(debug=True)