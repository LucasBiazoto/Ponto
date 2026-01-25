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
    data_hoje = agora.strftime('%d/%m/%Y')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # --- TRAVA DE DUPLICIDADE ---
        cur.execute('SELECT id FROM pontos WHERE data = %s AND tipo = %s', (data_hoje, tipo))
        if cur.fetchone():
            flash(f"Você já registrou sua {tipo} hoje! 🌸")
            return redirect(url_for('index'))
        
        cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                    (tipo, data_hoje, agora.strftime('%m'), agora.strftime('%H:%M'), "Via Site"))
        conn.commit()
        cur.close()
        conn.close()
        
        msg = "Bom trabalho meu bem" if tipo == 'Entrada' else "Bom descanso meu bem"
        flash(f"{msg} 🌸")
    except Exception as e:
        flash("Erro de conexão. Tente novamente.")
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
    minutos_totais_saldo = 0
    dias_completos = 0

    for data in sorted(dias.keys(), reverse=True):
        info = dias[data]
        cor, saldo_diario_str = "vermelho", "0.0h"
        
        if info['entrada'] and info['saida']:
            dias_completos += 1
            # Lógica exata de Minutos
            t1 = datetime.strptime(info['entrada'], '%H:%M')
            t2 = datetime.strptime(info['saida'], '%H:%M')
            minutos_trabalhados = (t2 - t1).total_seconds() / 60
            minutos_extra = minutos_trabalhados - 360 # 6h = 360 min
            minutos_totais_saldo += minutos_extra
            
            saldo_diario_str = f"{(minutos_extra/60):+.2f}h"
            
            if minutos_extra > 0: cor = "azul" 
            elif minutos_extra == 0: cor = "verde"
            else: cor = "vermelho"
        
        tabela_final.append({
            'data': data, 'entrada': info['entrada'], 'id_e': info['id_e'],
            'saida': info['saida'], 'id_s': info['id_s'], 
            'extra': saldo_diario_str, 'cor': cor
        })

    saldo_final_h = minutos_totais_saldo / 60
    return render_template('gestao.html', registros=tabela_final, mes_atual=mes_f, 
                           extras_mes=f"{saldo_final_h:+.2f}", dias=dias_completos)

# ... (Manter rotas de excluir, inserir_manual e exportar_pdf iguais)