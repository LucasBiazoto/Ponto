from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import pytz
import io
import json

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Base de dados (Lucas: Para produção, conecte ao Vercel Postgres)
historico_db = [] 

@app.route('/')
def index(): return render_template('index.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    # Lógica de agrupamento e cores (Verde, Azul, Vermelho)
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
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
            total_m += diff
            if diff == 0: cor = "#27ae60"
            elif diff > 0: cor = "#2980b9"
            else: cor = "#e74c3c"
            sinal = "+" if diff >= 0 else "-"
            saldo = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        tabela.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo})

    total_txt = f"{'+' if total_m >= 0 else '-'}{abs(total_m)//60:02d}:{abs(total_m)%60:02d}"
    return render_template('gestao.html', registros=tabela, total=total_txt, contador=dias_count, mes_atual=mes_f)

# --- NOVAS ROTAS PARA OS BOTÕES FUNCIONAREM ---

@app.route('/exportar_backup')
def exportar_backup():
    # Cria um arquivo JSON com todos os dados para segurança
    data = json.dumps(historico_db, indent=4)
    proxy = io.BytesIO(data.encode())
    return send_file(proxy, mimetype='application/json', as_attachment=True, download_name='backup_clinica.json')

@app.route('/exportar_pdf')
def exportar_pdf():
    # Gera um relatório simples em TXT (que pode ser salvo como PDF no navegador)
    relatorio = "RELATÓRIO DE PONTOS - Dra. Thamiris Araujo\n\n"
    for p in historico_db:
        relatorio += f"{p['data']} - {p['tipo']}: {p['hora']} (Local: {p['geo']})\n"
    proxy = io.BytesIO(relatorio.encode())
    return send_file(proxy, mimetype='text/plain', as_attachment=True, download_name='relatorio_pontos.txt')

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