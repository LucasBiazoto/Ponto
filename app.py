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
    # Puxa a URL do banco das variáveis que você já tem na Vercel
    url = os.environ.get('POSTGRES_URL')
    if url and "sslmode" not in url:
        url += "?sslmode=require"
    return psycopg2.connect(url)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Voltamos para o padrão "Via Site" sem coordenadas
        cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                    (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), "Via Site"))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"Bom {'trabalho' if tipo == 'Entrada' else 'descanso'} meu bem 🌸")
    except Exception as e:
        flash("Erro ao conectar com o banco de dados.")
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

    total_minutos_mes = 0
    dias_completos = 0
    tabela_final = []
    # Logica de resumo simplificada
    for r in registros_raw:
        tabela_final.append({'tipo': r[0], 'data': r[1], 'hora': r[2], 'geo': r[3], 'id': r[4]})
    
    return render_template('gestao.html', registros=tabela_final, mes_atual=mes_f, total="00:00", contador=len(tabela_final))

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