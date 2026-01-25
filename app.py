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
    # Tenta ler as variáveis comuns da Vercel/Neon
    url = os.environ.get('STORAGE_URL') or os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
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
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                    (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), "Via Site"))
        conn.commit()
        cur.close()
        conn.close()
        msg = "Bom trabalho meu bem" if tipo == 'Entrada' else "Bom descanso meu bem"
        flash(f"{msg} 🌸")
    except Exception as e:
        flash("Erro ao conectar ao banco de dados.")
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
            dias[data]['entrada'], dias[data]['id_e'] = hora, id_ponto
        else:
            dias[data]['saida'], dias[data]['id_s'] = hora, id_ponto

    tabela_final = []
    saldo_total_mes = 0.0
    dias_completos = 0

    for data in sorted(dias.keys(), reverse=True):
        info = dias[data]
        cor, h_extra_dia = "vermelho", 0.0
        
        if info['entrada'] and info['saida']:
            dias_completos += 1
            t1 = datetime.strptime(info['entrada'], '%H:%M')
            t2 = datetime.strptime(info['saida'], '%H:%M')
            horas_trab = (t2 - t1).total_seconds() / 3600
            h_extra_dia = horas_trab - 6
            saldo_total_mes += h_extra_dia
            
            if h_extra_dia > 0: cor = "azul" 
            elif h_extra_dia == 0: cor = "verde"
            else: cor = "vermelho"
        
        tabela_final.append({
            'data': data, 'entrada': info['entrada'], 'id_e': info['id_e'],
            'saida': info['saida'], 'id_s': info['id_s'], 
            'extra': f"{h_extra_dia:+.1f}", 'cor': cor
        })

    return render_template('gestao.html', registros=tabela_final, mes_atual=mes_f, 
                           extras_mes=f"{saldo_total_mes:+.1f}", dias=dias_completos)

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
    hora, tipo = request.form.get('hora'), request.form.get('tipo')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, data_f, data_f.split('/')[1], hora, "Manual (Gestora)"))
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
    cur.execute('SELECT data, tipo, hora FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros = cur.fetchall()
    cur.close()
    conn.close()

    dias_pdf = {}
    for r in registros:
        if r[0] not in dias_pdf: dias_pdf[r[0]] = {'e': '--:--', 's': '--:--'}
        if r[1] == 'Entrada': dias_pdf[r[0]]['e'] = r[2]
        else: dias_pdf[r[0]]['s'] = r[2]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Dra. Thamiris Araujo - Relatorio Mes {mes_f}", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(45, 10, "Data", 1); pdf.cell(45, 10, "Entrada", 1); pdf.cell(45, 10, "Saida", 1); pdf.cell(55, 10, "Saldo (Meta 6h)", 1)
    pdf.ln()

    total_h_mes = 0.0
    dias_ok = 0
    pdf.set_font("Arial", "", 10)
    for d in sorted(dias_pdf.keys()):
        e, s = dias_pdf[d]['e'], dias_pdf[d]['s']
        saldo_d = "0.0h"
        if e != '--:--' and s != '--:--':
            dias_ok += 1
            t1, t2 = datetime.strptime(e, '%H:%M'), datetime.strptime(s, '%H:%M')
            horas = (t2 - t1).total_seconds() / 3600
            total_h_mes += (horas - 6)
            saldo_d = f"{(horas-6):+.1f}h"
        
        pdf.cell(45, 10, d, 1); pdf.cell(45, 10, e, 1); pdf.cell(45, 10, s, 1); pdf.cell(55, 10, saldo_d, 1)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"Dias Trabalhados: {dias_ok}", ln=True)
    pdf.cell(190, 10, f"Saldo Final de Horas: {total_h_mes:+.1f}h", ln=True)
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(190, 10, "Desenvolvido por Lucas Biazoto", 0, 0, 'C')

    res = make_response(pdf.output(dest='S').encode('latin-1', 'ignore'))
    res.headers.set('Content-Disposition', 'attachment', filename=f'Relatorio_{mes_f}_DraThamiris.pdf')
    res.headers.set('Content-Type', 'application/pdf')
    return res

if __name__ == '__main__':
    app.run(debug=True)