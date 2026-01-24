from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import pytz
import io
import json

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Lucas: Esta lista DEVE ser substituída por um banco de dados real (Postgres)
# para que os dados da Dra. Thamiris parem de sumir a cada deploy.
historico_db = [] 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    # Lógica de agrupamento e Cores Triple (Verde, Azul, Vermelho)
    diario = {}
    for p in [x for x in historico_db if x['mes'] == mes_f]:
        d = p['data']
        if d not in diario: diario[d] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if p['tipo'] == 'Entrada': 
            diario[d]['e'] = p['hora']; diario[d]['id_e'] = p['id']
        else: 
            diario[d]['s'] = p['hora']; diario[d]['id_s'] = p['id']

    total_m = 0
    dias_count = 0
    tabela = []

    for data, v in diario.items():
        cor, saldo = "#5a4a4d", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_count += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360 # Jornada 6h
            total_m += diff
            
            # Lógica de cores solicitada
            if diff == 0: cor = "#27ae60" # VERDE
            elif diff > 0: cor = "#2980b9" # AZUL
            else: cor = "#e74c3c" # VERMELHO
            
            sinal = "+" if diff >= 0 else "-"
            saldo = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        tabela.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo})

    total_txt = f"{'+' if total_m >= 0 else '-'}{abs(total_m)//60:02d}:{abs(total_m)%60:02d}"
    return render_template('gestao.html', registros=tabela, total=total_txt, contador=dias_count, mes_atual=mes_f)

# --- FUNÇÕES DOS BOTÕES QUE ESTAVAM FALTANDO ---

@app.route('/exportar_backup')
def exportar_backup():
    # Gera um arquivo com todos os registros para segurança
    data = json.dumps(historico_db, indent=4)
    proxy = io.BytesIO(data.encode())
    return send_file(proxy, mimetype='application/json', as_attachment=True, download_name='backup_ponto.json')

@app.route('/exportar_pdf')
def exportar_pdf():
    # Gera um relatório em texto (PDF simples)
    txt = "RELATÓRIO DE PONTO - DRA. THAMIRIS ARAUJO\n\n"
    for r in historico_db:
        txt += f"{r['data']} | {r['tipo']}: {r['hora']}\n"
    proxy = io.BytesIO(txt.encode())
    return send_file(proxy, mimetype='text/plain', as_attachment=True, download_name='relatorio_ponto.txt')

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico_db
    historico_db = [p for p in historico_db if p['id'] != id]
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