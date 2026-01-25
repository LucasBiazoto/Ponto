import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from datetime import datetime
import pytz
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    url = os.environ.get('POSTGRES_URL')
    if url and "sslmode" not in url:
        url += "?sslmode=require"
    return psycopg2.connect(url)

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), "Via Site"))
    conn.commit()
    cur.close()
    conn.close()
    flash(f"Bom {'trabalho' if tipo == 'Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT tipo, data, hora, geo, id FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close()
    conn.close()

    tabela_final = []
    pontos_por_dia = {}
    
    for r in registros_raw:
        item = {'tipo': r[0], 'data': r[1], 'hora': r[2], 'geo': r[3], 'id': r[4]}
        tabela_final.append(item)
        if r[1] not in pontos_por_dia: pontos_por_dia[r[1]] = []
        pontos_por_dia[r[1]].append(item)

    # Lógica de Horas Extras (Meta 6h)
    total_segundos = 0
    for data, pontos in pontos_por_dia.items():
        ents = [p for p in pontos if p['tipo'] == 'Entrada']
        sais = [p for p in pontos if p['tipo'] == 'Saída']
        for e, s in zip(ents, sais):
            try:
                t1 = datetime.strptime(e['hora'], '%H:%M')
                t2 = datetime.strptime(s['hora'], '%H:%M')
                total_segundos += (t2 - t1).total_seconds()
            except: continue

    total_h = total_segundos / 3600
    dias_trab = len(pontos_por_dia)
    meta = dias_trab * 6
    extras = total_h - meta

    return render_template('gestao.html', registros=tabela_final[::-1], mes_atual=mes_f, 
                           total_h=f"{total_h:.1f}", extras=f"{extras:.1f}", dias=dias_trab)

@app.route('/excluir/<int:id>')
def excluir(id):
    if not session.get('admin_logado'): return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_raw = request.form.get('data')
    data_f = datetime.strptime(data_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
    mes = data_f.split('/')[1]
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, data_f, mes, hora, "Manual"))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/exportar_pdf')
def exportar_pdf():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT data, tipo, hora, geo FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    dados = cur.fetchall()
    cur.close()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio Dra Thamiris Araujo - Mes {mes_f}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "Data", 1); pdf.cell(40, 10, "Tipo", 1); pdf.cell(40, 10, "Hora", 1); pdf.cell(70, 10, "Obs", 1)
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for r in dados:
        pdf.cell(40, 10, str(r[0]), 1); pdf.cell(40, 10, str(r[1]), 1); pdf.cell(40, 10, str(r[2]), 1); pdf.cell(70, 10, str(r[3]), 1)
        pdf.ln()
    
    res = make_response(pdf.output(dest='S').encode('latin-1', 'ignore'))
    res.headers.set('Content-Disposition', 'attachment', filename=f'Relatorio_{mes_f}.pdf')
    res.headers.set('Content-Type', 'application/pdf')
    return res

if __name__ == '__main__':
    app.run(debug=True)