from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import pytz
import io
import json

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Base de dados temporária
historico_db = [] 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    try:
        tipo = request.form.get('tipo')
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        agora = datetime.now(fuso)
        
        historico_db.append({
            'id': len(historico_db) + 1,
            'tipo': tipo,
            'data': agora.strftime('%d/%m/%Y'),
            'mes': agora.strftime('%m'),
            'hora': agora.strftime('%H:%M'),
            'geo': f"{lat}, {lon}" if lat and lat != "" else "GPS Desativado"
        })
        
        flash("Bom trabalho meu bem 🌸" if tipo == 'Entrada' else "Bom descanso meu bem 🌸")
        return redirect(url_for('index'))
    except:
        return "Erro ao processar ponto", 500

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    # Lógica de processamento da tabela (mesmo código anterior)
    # ... (código de cálculo de horas) ...
    return render_template('gestao.html', registros=[], total="00:00", contador=0, mes_atual=mes_f)

# --- CORREÇÃO DOS ERROS DE DOWNLOAD ---
@app.route('/exportar_backup')
def exportar_backup():
    data = json.dumps(historico_db, indent=4)
    return send_file(io.BytesIO(data.encode()), mimetype='application/json', as_attachment=True, download_name='backup.json')

@app.route('/exportar_pdf')
def exportar_pdf():
    txt = "RELATORIO DE PONTO\n"
    for r in historico_db: txt += f"{r['data']} - {r['tipo']}: {r['hora']}\n"
    return send_file(io.BytesIO(txt.encode()), mimetype='text/plain', as_attachment=True, download_name='relatorio.txt')

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