import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    if url and "sslmode" not in url:
        url += "?sslmode=require"
    return psycopg2.connect(url)

def formatar_saldo(minutos_totais):
    sinal = "+" if minutos_totais >= 0 else "-"
    m_abs = abs(int(minutos_totais))
    h = m_abs // 60
    m = m_abs % 60
    return f"{sinal}{h}h {m:02d}m"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "8340":
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
        flash("Senha incorreta!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    data_hoje = agora.strftime('%d/%m/%Y')
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute('SELECT id FROM pontos WHERE data = %s AND tipo = %s', (data_hoje, tipo))
        if cur.fetchone():
            flash(f"Registro de {tipo} ja feito hoje! 🌸")
            return redirect(url_for('index'))
        cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                    (tipo, data_hoje, agora.strftime('%m'), agora.strftime('%H:%M'), "Site"))
        conn.commit(); cur.close(); conn.close()
        flash("Bom trabalho meu bem 🌸" if tipo == 'Entrada' else "Bom descanso meu bem 🌸")
    except:
        flash("Erro de conexao.")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('SELECT data, tipo, hora, id FROM pontos WHERE mes = %s ORDER BY data DESC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close(); conn.close()

    dias = {}
    for r in registros_raw:
        data, tipo, hora, id_ponto = r
        if data not in dias: dias[data] = {'entrada': None, 'saida': None, 'id_e': None, 'id_s': None}
        if tipo == 'Entrada': dias[data]['entrada'], dias[data]['id_e'] = hora, id_ponto
        else: dias[data]['saida'], dias[data]['id_s'] = hora, id_ponto

    tabela = []
    minutos_total = 0
    for d in sorted(dias.keys(), reverse=True):
        info = dias[d]
        saldo_str, cor = "0h 00m", "verde"
        if info['entrada'] and info['saida']:
            t1 = datetime.strptime(info['entrada'], '%H:%M')
            t2 = datetime.strptime(info['saida'], '%H:%M')
            saldo_dia = ((t2 - t1).total_seconds() / 60) - 360 # Jornada 6h
            minutos_total += saldo_dia
            saldo_str = formatar_saldo(saldo_dia)
            if saldo_dia > 0: cor = "azul"
            elif saldo_dia < 0: cor = "vermelho"
            else: cor = "verde"
            
        tabela.append({'data': d, 'entrada': info['entrada'], 'saida': info['saida'], 
                       'id_e': info['id_e'], 'id_s': info['id_s'], 'extra': saldo_str, 'cor': cor})

    return render_template('gestao.html', registros=tabela, mes_atual=mes_f, 
                           extras_mes=formatar_saldo(minutos_total), dias=len(dias))

@app.route('/backup')
def backup():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute('SELECT id, tipo, data, mes, hora, geo FROM pontos ORDER BY id ASC')
        dados = cur.fetchall()
        cur.close(); conn.close()
        lista = [{"id": d[0], "tipo": d[1], "data": d[2], "mes": d[3], "hora": d[4], "origem": d[5]} for d in dados]
        return jsonify(lista)
    except:
        return "Erro ao processar backup."

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_f = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (request.form.get('tipo'), data_f, data_f.split('/')[1], request.form.get('hora'), "Manual"))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if not session.get('admin_logado'): return redirect(url_for('login'))
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('DELETE FROM pontos WHERE id = %s', (id,)); conn.commit()
    cur.close(); conn.close()
    return redirect(url_for('gestao'))