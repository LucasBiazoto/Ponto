import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    return psycopg2.connect(os.environ.get('POSTGRES_URL'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora) VALUES (%s, %s, %s, %s)',
                (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M')))
    conn.commit()
    cur.close()
    conn.close()
    flash("Bom trabalho meu bem 🌸" if tipo == 'Entrada' else "Bom descanso meu bem 🌸")
    return redirect(url_for('index'))

# ROTA QUE ESTAVA FALTANDO PARA O PONTO MANUAL
@app.route('/ponto_manual', methods=['POST'])
def ponto_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_f = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    mes_f = data_f.split('/')[1]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora) VALUES (%s, %s, %s, %s)',
                (request.form.get('tipo'), data_f, mes_f, request.form.get('hora')))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT tipo, data, hora, id FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close()
    conn.close()

    diario = {}
    for tipo, data, hora, p_id in registros_raw:
        if data not in diario: diario[data] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if tipo == 'Entrada': diario[data]['e'], diario[data]['id_e'] = hora, p_id
        else: diario[data]['s'], diario[data]['id_s'] = hora, p_id

    total_minutos_mes, dias_completos, tabela_final = 0, 0, []

    for data in sorted(diario.keys()):
        v = diario[data]
        cor, saldo_dia_str = "#d68c9a", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360 # Base 6h
            total_minutos_mes += diff
            cor = "#2980b9" if diff > 0 else ("#27ae60" if diff == 0 else "#e74c3c")
            sinal = "+" if diff >= 0 else "-"
            saldo_dia_str = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        tabela_final.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo_dia_str})

    total_txt = f"{'+' if total_minutos_mes >= 0 else '-'}{abs(total_minutos_mes)//60:02d}:{abs(total_minutos_mes)%60:02d}"
    return render_template('gestao.html', registros=tabela_final[::-1], total=total_txt, contador=dias_completos, mes_atual=mes_f)

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == "8340":
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))