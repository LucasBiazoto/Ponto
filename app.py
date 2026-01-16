import sqlite3
import pandas as pd
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify

app = Flask(__name__)

def get_agora_brasil():
    fuso = timezone(timedelta(hours=-3))
    return datetime.now(fuso)

def get_db_connection():
    conn = sqlite3.connect('ponto.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, tipo TEXT, horario TEXT, data_texto TEXT, localizacao TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS colaboradoras 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)''')
    
    # --- COMANDO PARA LIMPAR TESTES E REINICIAR COM ESTHER ---
    conn.execute("DELETE FROM colaboradoras WHERE nome LIKE 'Lucas%'")
    try:
        conn.execute("INSERT OR IGNORE INTO colaboradoras (nome) VALUES ('Esther Julia')")
    except: pass
    # -------------------------------------------------------
    
    conn.commit()
    conn.close()

def formatar_horas_bonito(decimal_horas):
    sinal = "+" if decimal_horas >= 0 else "-"
    total_minutos = abs(int(round(decimal_horas * 60)))
    h = total_minutos // 60
    m = total_minutos % 60
    return f"{sinal}{h}h {m}min"

def calcular_jornada(entrada_str, saida_str):
    formato = "%d/%m/%Y %H:%M"
    try:
        inicio = datetime.strptime(entrada_str[:16], formato)
        fim = datetime.strptime(saida_str[:16], formato)
        diff = fim - inicio
        horas = diff.total_seconds() / 3600
        return round(horas, 2), round(horas - 6.0, 2)
    except: return 0, 0

@app.route('/')
def index():
    conn = get_db_connection()
    colab = [row['nome'] for row in conn.execute("SELECT nome FROM colaboradoras ORDER BY nome ASC").fetchall()]
    conn.close()
    return render_template('index.html', colaboradoras=colab)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('nome'); tipo = request.form.get('tipo')
    lat = request.form.get('lat'); lon = request.form.get('lon')
    CLINICA_LAT, CLINICA_LON = -23.5255, -46.5273
    status_local = "✅ Ok"
    if lat and lon:
        distancia = ((float(lat) - CLINICA_LAT)**2 + (float(lon) - CLINICA_LON)**2)**0.5
        if distancia > 0.005: status_local = "📍 Fora"
    else: status_local = "❓ Sem GPS"
    
    agora = get_agora_brasil()
    horario_ponto = agora.strftime("%d/%m/%Y %H:%M")
    conn = get_db_connection()
    conn.execute("INSERT INTO registros (nome, tipo, horario, data_texto, localizacao) VALUES (?, ?, ?, ?, ?)", 
                 (nome, tipo, horario_ponto, agora.strftime("%d/%m/%Y"), status_local))
    conn.commit(); conn.close()
    
    msg = "Bom trabalho meu bem" if tipo == "Entrada" else "Bom descanso meu bem"
    return jsonify({"status":"SUCESSO","msg_destaque":msg,"msg_sub":f"Horário: {horario_ponto.split(' ')[1]}"})

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('senha') != '8340': return redirect(url_for('index'))
    agora_br = get_agora_brasil()
    mes = request.args.get('mes', agora_br.strftime("%m"))
    ano = request.args.get('ano', agora_br.strftime("%Y"))
    
    conn = get_db_connection()
    colab_lista = conn.execute("SELECT * FROM colaboradoras ORDER BY nome ASC").fetchall()
    relatorio = []; presentes = []; total_extras_periodo = 0.0
    termo_busca = f"%/{mes}/{ano}%"
    
    for c in colab_lista:
        regs = conn.execute("SELECT tipo, horario FROM registros WHERE nome = ? AND horario LIKE ?", (c['nome'], termo_busca)).fetchall()
        if regs and regs[-1]['tipo'] == 'Entrada' and regs[-1]['horario'].startswith(agora_br.strftime("%d/%m/%Y")):
            presentes.append(c['nome'])
        
        datas = sorted(list(set([r['horario'].split(' ')[0] for r in regs])))
        total_saldo_ind = 0.0; dias = 0
        for d in datas:
            e = [r['horario'] for r in regs if r['horario'].startswith(d) and r['tipo'] == 'Entrada']
            s = [r['horario'] for r in regs if r['horario'].startswith(d) and r['tipo'] == 'Saída']
            if e and s:
                dias += 1; _, saldo = calcular_jornada(e[0], s[-1]); total_saldo_ind += saldo
        
        total_extras_periodo += total_saldo_ind
        relatorio.append({'id':c['id'],'nome':c['nome'],'dias':dias,'saldo_decimal':total_saldo_ind,'saldo_formatado':formatar_horas_bonito(total_saldo_ind)})
    
    ultimos = conn.execute("SELECT * FROM registros ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return render_template('admin.html', relatorio=relatorio, ultimos=ultimos, colaboradoras=colab_lista, mes_sel=mes, ano_sel=ano, presentes=presentes, total_extras=formatar_horas_bonito(total_extras_periodo))

@app.route('/excluir_colaboradora/<int:id>')
def excluir_colaboradora(id):
    conn = get_db_connection(); conn.execute("DELETE FROM registros WHERE nome = (SELECT nome FROM colaboradoras WHERE id = ?)", (id,)); conn.execute("DELETE FROM colaboradoras WHERE id = ?", (id,)); conn.commit(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/cadastrar_colaboradora', methods=['POST'])
def cadastrar():
    n = request.form.get('nome_novo')
    if n:
        conn = get_db_connection()
        try: conn.execute("INSERT OR IGNORE INTO colaboradoras (nome) VALUES (?)", (n.strip(),)); conn.commit()
        except: pass
        conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/lancar_manual', methods=['POST'])
def lancar_manual():
    n = request.form.get('nome'); t = request.form.get('tipo'); dt = request.form.get('data_hora').strip()
    conn = get_db_connection(); conn.execute("INSERT INTO registros (nome, tipo, horario, data_texto, localizacao) VALUES (?,?,?,?,?)", (n,t,dt,dt.split(' ')[0],"📝 Manual")); conn.commit(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

@app.route('/exportar')
def exportar():
    conn = get_db_connection(); df = pd.read_sql_query("SELECT * FROM registros", conn); conn.close()
    df.to_excel("Relatorio_Estetica.xlsx", index=False); return send_file("Relatorio_Estetica.xlsx", as_attachment=True)

@app.route('/backup')
def backup(): return send_file("ponto.db", as_attachment=True)

@app.route('/excluir_ponto/<int:id>')
def excluir_ponto(id):
    conn = get_db_connection(); conn.execute("DELETE FROM registros WHERE id = ?", (id,)); conn.commit(); conn.close()
    return redirect(url_for('painel_gestao', senha='8340'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)