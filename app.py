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
    # Certifique-se de que a variável POSTGRES_URL está configurada na Vercel
    return psycopg2.connect(os.environ.get('POSTGRES_URL'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    # Captura opcional de latitude/longitude se o navegador permitir
    lat = request.form.get('lat') or '0'
    lon = request.form.get('lon') or '0'
    
    agora = datetime.now(fuso)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), f"{lat}, {lon}"))
    conn.commit()
    cur.close()
    conn.close()
    
    flash("Bom trabalho meu bem 🌸" if tipo == 'Entrada' else "Bom descanso meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/ponto_manual', methods=['POST'])
def ponto_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Converte data do formulário (YYYY-MM-DD) para o padrão brasileiro
    data_raw = request.form.get('data')
    data_f = datetime.strptime(data_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
    mes_f = data_f.split('/')[1]
    hora_f = request.form.get('hora')
    tipo_f = request.form.get('tipo')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo_f, data_f, mes_f, hora_f, "Inserção Manual"))
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
        if data not in diario: 
            diario[data] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if tipo == 'Entrada': 
            diario[data]['e'], diario[data]['id_e'] = hora, p_id
        else: 
            diario[data]['s'], diario[data]['id_s'] = hora, p_id

    total_minutos_mes = 0
    dias_completos = 0
    tabela_final = []

    for data in sorted(diario.keys()):
        v = diario[data]
        cor = "#5a4a4d" # Cor neutra para pontos incompletos
        saldo_dia_str = "00:00"
        
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            
            # CÁLCULO DE 6 HORAS (360 MINUTOS)
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
            total_minutos_mes += diff
            
            # Lógica de Cores: Azul (+), Verde (Cravado), Vermelho (-)
            if diff > 0: cor = "#2980b9"
            elif diff == 0: cor = "#27ae60"
            else: cor = "#e74c3c"
            
            sinal = "+" if diff >= 0 else "-"
            saldo_dia_str = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        tabela_final.append({
            'data': data, 'e': v['e'], 's': v['s'], 
            'id_e': v['id_e'], 'id_s': v['id_s'], 
            'cor': cor, 'saldo': saldo_dia_str
        })

    sinal_total = "+" if total_minutos_mes >= 0 else "-"
    total_txt = f"{sinal_total}{abs(total_minutos_mes)//60:02d}:{abs(total_minutos_mes)%60:02d}"
    
    return render_template('gestao.html', registros=tabela_final[::-1], total=total_txt, contador=dias_completos, mes_atual=mes_f)

@app.route('/exportar_pdf')
def exportar_pdf():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT data, tipo, hora FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros = cur.fetchall()
    cur.close()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio Dra Thamiris Araujo - Mes {mes_f}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, "Data", 1)
    pdf.cell(60, 10, "Tipo", 1)
    pdf.cell(70, 10, "Hora", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 12)
    for r in registros:
        pdf.cell(60, 10, str(r[0]), 1)
        pdf.cell(60, 10, str(r[1]), 1)
        pdf.cell(70, 10, str(r[2]), 1)
        pdf.ln()
    
    response = make_response(pdf.output(dest='S').encode('latin-1', 'ignore'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'Relatorio_Thamiris_Mes_{mes_f}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

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