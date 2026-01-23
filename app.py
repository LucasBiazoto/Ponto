from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'
ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')

registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    loc = request.form.get('local_status') or "Unidade Penha"
    agora = datetime.now(fuso_horario)
    
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': loc
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem! 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': request.form.get('nome'), 
        'tipo': request.form.get('tipo'),
        'data': data_br, 
        'hora': request.form.get('hora'),
        'local': 'Manual pela Gestão'
    })
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    resumo = {}
    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None, 'loc': 'N/A'}
        if r['tipo'] == 'Entrada':
            resumo[chave]['e'] = r['hora']
            resumo[chave]['id_e'] = r['id']
            resumo[chave]['loc'] = r.get('local', 'N/A')
        else:
            resumo[chave]['s'] = r['hora']
            resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo_str = "00:00"
        cor_status = "azul" 
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
                if diff > 0: cor_status = "verde"
                elif diff < 0: cor_status = "vermelho"
                else: cor_status = "azul"
                sinal = "+" if diff >= 0 else "-"
                abs_m = abs(diff)
                saldo_str = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            except: pass
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'],
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo_str, 
            'loc': v['loc'], 'cor': cor_status
        })
    return render_template('gestao.html', registros=dados_finais)

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))