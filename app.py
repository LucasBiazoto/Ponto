from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from datetime import datetime
import pytz
import json

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_permanente_key'
fuso = pytz.timezone('America/Sao_Paulo')

# Endereço da Clínica conforme solicitado
ENDERECO_PENHA = "Av. Amador Bueno da Veiga, 1230 - Penha"

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
        'id': len(registros_ponto) + 1,
        'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': ENDERECO_PENHA
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    try:
        data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
        registros_ponto.append({
            'id': len(registros_ponto) + 1,
            'nome': request.form.get('nome'),
            'tipo': request.form.get('tipo'),
            'data': data_br,
            'hora': request.form.get('hora'),
            'local': "Manual - " + ENDERECO_PENHA
        })
    except: pass
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    resumo = {}
    total_minutos = 0

    for r in registros_ponto:
        if r['data'].split('/')[1] == mes_sel:
            chave = (r['data'], r['nome'])
            if chave not in resumo:
                resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
            if r['tipo'] == 'Entrada':
                resumo[chave]['e'] = r['hora']; resumo[chave]['id_e'] = r['id']
            else:
                resumo[chave]['s'] = r['hora']; resumo[chave]['id_s'] = r['id']

    dados_finais = []
    dias_completos = 0 # NOVA LÓGICA DE CONTAGEM

    for (data, nome), v in resumo.items():
        cor, saldo = "azul", "00:00"
        # SÓ CONTA DIA SE TIVER ENTRADA E SAÍDA
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
                total_minutos += diff
                cor = "verde" if diff > 0 else "vermelho" if diff < 0 else "azul"
                saldo = f"{'+' if diff >= 0 else '-'}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
            except: pass
        
        dados_finais.append({'data': data, 'nome': nome, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo, 'cor': cor})

    s_total = f"{'+' if total_minutos >= 0 else '-'}{abs(total_minutos)//60:02d}:{abs(total_minutos)%60:02d}"
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, mes_sel=mes_sel, qtd_dias=dias_completos)

@app.route('/backup')
def backup():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    return Response(json.dumps(registros_ponto, indent=4), mimetype="application/json",
                    headers={"Content-disposition": "attachment; filename=backup_clinica.json"})

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
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