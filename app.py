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
    cur.execute('SELECT data, tipo, hora, id FROM pontos WHERE mes = %s ORDER BY data DESC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close()
    conn.close()

    dias = {}
    for r in registros_raw:
        data, tipo, hora, id_ponto = r
        if data not in dias:
            dias[data] = {'entrada': None, 'saida': None, 'id_e': None, 'id_s': None}
        if tipo == 'Entrada':
            dias[data]['entrada'] = hora
            dias[data]['id_e'] = id_ponto
        else:
            dias[data]['saida'] = hora
            dias[data]['id_s'] = id_ponto

    tabela_final = []
    total_segundos_mes = 0
    dias_completos = 0

    for data in sorted(dias.keys(), reverse=True):
        info = dias[data]
        cor = "vermelho"
        h_extra = "0.0"
        
        if info['entrada'] and info['saida']:
            dias_completos += 1
            t1 = datetime.strptime(info['entrada'], '%H:%M')
            t2 = datetime.strptime(info['saida'], '%H:%M')
            segundos_dia = (t2 - t1).total_seconds()
            total_segundos_mes += segundos_dia
            horas_dia = segundos_dia / 3600
            saldo = horas_dia - 6
            h_extra = f"{saldo:+.1f}"
            
            if saldo > 0: cor = "azul"
            elif saldo == 0: cor = "verde"
            else: cor = "vermelho"
        
        tabela_final.append({
            'data': data, 'entrada': info['entrada'], 'id_e': info['id_e'],
            'saida': info['saida'], 'id_s': info['id_s'], 'extra': h_extra, 'cor': cor
        })

    total_h = total_segundos_mes / 3600
    extras_total = total_h - (dias_completos * 6)

    return render_template('gestao.html', registros=tabela_final, mes_atual=mes_f, 
                           total_h=f"{total_h:.1f}", extras=f"{extras_total:.1f}", dias=dias_completos)

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM pontos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    data_f = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    hora, tipo = request.form.get('hora'), request.form.get('tipo')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, data_f, data_f.split('/')[1], hora, "Manual"))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('gestao'))

@app.route('/exportar_pdf')
def exportar_pdf():
    # Lógica de PDF simplificada (pode ser expandida conforme necessidade)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "Relatorio de Pontos - Dra. Thamiris Araujo", ln=True, align="C")
    res = make_response(pdf.output(dest='S').encode('latin-1'))
    res.headers.set('Content-Disposition', 'attachment', filename='relatorio.pdf')
    res.headers.set('Content-Type', 'application/pdf')
    return res

if __name__ == '__main__':
    app.run(debug=True)