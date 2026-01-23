from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista temporária de registros
registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat', '')
    lon = request.form.get('lon', '')
    agora = datetime.now(fuso)
    
    registros_ponto.append({
        'id': len(registros_ponto) + 1,
        'nome': "Esther Julia",
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': "Na Clínica" if lat and lon else "GPS Off"
    })
    
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == "8340":
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    resumo = {}
    total_minutos = 0
    dias_completos = 0

    for r in registros_ponto:
        if r['data'].split('/')[1] == mes_sel:
            data = r['data']
            if data not in resumo:
                resumo[data] = {'e': '--:--', 's': '--:--', 'id': r['id']}
            if r['tipo'] == 'Entrada': resumo[data]['e'] = r['hora']
            else: resumo[data]['s'] = r['hora']

    dados_finais = []
    for data, v in resumo.items():
        saldo, cor = "00:00", "azul"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
            total_minutos += diff
            saldo = f"{'+' if diff >= 0 else '-'}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
            cor = "verde" if diff >= 0 else "vermelho"
        dados_finais.append({'data': data, 'e': v['e'], 's': v['s'], 'saldo': saldo, 'cor': cor, 'id': v['id']})

    s_total = f"{'+' if total_minutos >= 0 else '-'}{abs(total_minutos)//60:02d}:{abs(total_minutos)%60:02d}"
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, qtd_dias=dias_completos, mes_sel=mes_sel)

@app.route('/excluir/<int:id>')
def excluir(id):
    if not session.get('admin_logado'): return redirect(url_for('login'))
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))