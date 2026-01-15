import sqlite3
import pandas as pd
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify

app = Flask(__name__)
app.secret_key = 'dra_thamiris_luxury_final_2026'

# --- BANCO DE DADOS ---
def get_db_connection():
    conn = sqlite3.connect('ponto.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS registros 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome TEXT, tipo TEXT, horario TEXT, 
                       data_texto TEXT, localizacao TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS colaboradoras 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome TEXT UNIQUE)''')
    conn.commit()
    conn.close()

# --- LÓGICA DE CÁLCULO (Jornada de 6h) ---
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

# --- ROTAS ---

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
    
    # Localização da Clínica (Tatuapé/SP)
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
    
    # Mensagens Personalizadas Dra. Thamiris
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return jsonify({"status": "SUCESSO", "msg_destaque": msg, "msg_sub": f"Local: {status_local}", "fora": fora})

@app.route('/painel_gestao')
def painel_gestao():
    senha_digitada = request.args.get('senha')
    
    # --- TELA DE PEDIR SENHA (CAIXINHA) ---
    if senha_digitada != '8340':
        return """
        <body style="background:#fffafb; font-family:sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0;">
            <div style="background:white; padding:40px; border-radius:25px; box-shadow:0 10px 30px rgba(212,165,178,0.2); text-align:center; max-width:320px; width:90%;">
                <h3 style="color:#b5838d; margin-bottom:10px; font-weight:300;">🌸 Área Restrita</h3>
                <p style="color:#888; font-size:0.9rem; margin-bottom:25px;">Por favor, digite a senha de gestão da clínica.</p>
                <form action="/painel_gestao" method="get">
                    <input type="password" name="senha" placeholder="Senha" autofocus
                           style="padding:12px; border-radius:12px; border:1px solid #f8ecee; margin-bottom:15px; width:100%; outline:none; text-align:center;">
                    <button type="submit" style="background:#d4a5b2; color:white; border:none; padding:12px; width:100%; border-radius:12px; cursor:pointer; font-weight:bold;">Acessar Painel</button>
                </form>
                <br><a href="/" style="color:#d4a5b2; text-decoration:none; font-size:0.8rem;">Voltar ao início</a>
            </div>
        </body>
        """, 403

    mes = request.args.get('mes', datetime.now().strftime("%m"))
    filtro = f"/{mes}/{datetime.now().strftime('%Y')}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM colaboradoras ORDER BY nome ASC")
    colab_lista = cursor.fetchall()
    
    relatorio = []
    total_extras_mes = 0.0
    
    for c in colab_lista:
        n = c['nome']
        cursor.execute("SELECT tipo, horario FROM registros WHERE nome = ? AND horario LIKE ?", (n, f"%{filtro}%"))
        regs = cursor.fetchall()
            
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
        relatorio.append({'id': c['id'], 'nome': n, 'dias': dias, 'saldo': round(total_saldo, 2)})
    
    cursor.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 100")
    ultimos = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', relatorio=relatorio, ultimos=ultimos, mes_sel=mes, total_extras=round(total_extras_mes, 1))

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
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/excluir_colaboradora/<int:id>')
def excluir_colaboradora(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM colaboradoras WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = ?", (id,))
    conn.commit()
    conn.close()
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