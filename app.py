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
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), "Via Site"))
    conn.commit()
    cur.close()
    conn.close()
    flash(f"Bom {'trabalho' if tipo == 'Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/ponto_manual', methods=['POST'])
def ponto_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_raw = request.form.get('data')
    data_f = datetime.strptime(data_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
    hora_f = request.form.get('hora')
    tipo_f = request.form.get('tipo')
    mes_f = data_f.split('/')[1]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo_f, data_f, mes_f, hora_f, "Ponto Manual"))
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
    cur.execute('SELECT tipo, data, hora, geo, id FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close()
    conn.close()

    diario = {}
    for tipo, data, hora, geo, p_id in registros_raw:
        if data not in diario: 
            diario[data] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None, 'status': geo}
        if tipo == 'Entrada': 
            diario[data]['e'], diario[data]['id_e'] = hora, p_id
        else: 
            diario[data]['s'], diario[data]['id_s'] = hora, p_id
        if "Manual" in geo: diario[data]['status'] = "Ponto Manual"

    total_minutos_mes = 0
    dias_completos = 0
    tabela_final = []

    for data in sorted(diario.keys()):
        v = diario[data]
        cor, saldo_dia_str = "#5a4a4d", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
            total_minutos_mes += diff
            if diff > 0: cor = "#2980b9" # Azul Extra
            elif diff == 0: cor = "#27ae60" # Verde OK
            else: cor = "#e74c3c" # Vermelho Devendo
            sinal = "+" if diff >= 0 else "-"
            saldo_dia_str = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        tabela_final.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo_dia_str, 'status': v['status']})

    sinal_total = "+" if total_minutos_mes >= 0 else "-"
    total_txt = f"{sinal_total}{abs(total_minutos_mes)//60:02d}:{abs(total_minutos_mes)%60:02d}"
    return render_template('gestao.html', registros=tabela_final[::-1], total=total_txt, contador=dias_completos, mes_atual=mes_f)

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
    pdf.cell(40, 10, "Data", 1); pdf.cell(40, 10, "Tipo", 1); pdf.cell(40, 10, "Hora", 1); pdf.cell(70, 10, "Observacao", 1)
    pdf.ln()
    pdf.set_font("Arial", "", 10)
    for r in dados:
        pdf.cell(40, 10, str(r[0]), 1); pdf.cell(40, 10, str(r[1]), 1); pdf.cell(40, 10, str(r[2]), 1); pdf.cell(70, 10, str(r[3]), 1)
        pdf.ln()
    
    res = make_response(pdf.output(dest='S').encode('latin-1', 'ignore'))
    res.headers.set('Content-Disposition', 'attachment', filename=f'Relatorio_Mes_{mes_f}.pdf')
    res.headers.set('Content-Type', 'application/pdf')
    return res

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

if __name__ == '__main__':
    app.run(debug=True)