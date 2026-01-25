import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from datetime import datetime
import pytz
from fpdf import FPDF # Adicione esta linha

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    return psycopg2.connect(os.environ.get('POSTGRES_URL'))

# --- NOVA ROTA PARA PDF ---
@app.route('/exportar_pdf')
def exportar_pdf():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT tipo, data, hora FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros = cur.fetchall()
    cur.close()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Relatorio de Pontos - Mes {mes_f}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, "Data", 1)
    pdf.cell(60, 10, "Tipo", 1)
    pdf.cell(70, 10, "Hora", 1)
    pdf.ln()
    pdf.set_font("Arial", "", 12)
    for r in registros:
        pdf.cell(60, 10, r[1], 1)
        pdf.cell(60, 10, r[0], 1)
        pdf.cell(70, 10, r[2], 1)
        pdf.ln()
    
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'pontos_mes_{mes_f}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response

# Mantenha as rotas de bater_ponto, ponto_manual, gestao e login exatamente como estão 
# para não perder a lógica de cores e cálculos que já funciona!