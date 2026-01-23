from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'
fuso = pytz.timezone('America/Sao_Paulo')

registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    registros_ponto.append({
        'id': len(registros_ponto), 'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'), 'hora': agora.strftime('%H:%M'), 'loc': 'Unidade Penha'
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    resumo = {}
    total_minutos = 0
    for r in registros_ponto:
        if datetime.strptime(r['data'], '%d/%m/%Y').strftime('%m') == mes_sel:
            chave = (r['data'], r['nome'])
            if chave not in resumo: resumo[chave] = {'e':'--:--','s':'--:--','id_e':None,'id_s':None}
            if r['tipo'] == 'Entrada': resumo[chave]['e']=r['hora']; resumo[chave]['id_e']=r['id']
            else: resumo[chave]['s']=r['hora']; resumo[chave]['id_s']=r['id']

    dados = []
    for (data, nome), v in resumo.items():
        cor, saldo = "azul", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            h1, m1 = map(int, v['e'].split(':')); h2, m2 = map(int, v['s'].split(':'))
            diff = (h2*60+m2) - (h1*60+m1) - 360
            total_minutos += diff
            cor = "verde" if diff > 0 else "vermelho" if diff < 0 else "azul"
            saldo = f"{'+' if diff>=0 else '-'}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        dados.append({'data':data,'nome':nome,'e':v['e'],'s':v['s'],'id_e':v['id_e'],'id_s':v['id_s'],'saldo':saldo,'cor':cor})
    
    s_total = f"{'+' if total_minutos>=0 else '-'}{abs(total_minutos)//60:02d}:{abs(total_minutos)%60:02d}"
    return render_template('gestao.html', registros=dados, soma_total=s_total, mes_sel=mes_sel)

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    registros_ponto.append({
        'id': len(registros_ponto), 'nome': request.form.get('nome'), 'tipo': request.form.get('tipo'),
        'data': data_br, 'hora': request.form.get('hora'), 'loc': 'Manual pela Gestão'
    })
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