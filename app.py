from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista temporária (O Lucas deve conectar um Banco de Dados SQL para não perder dados)
db_pontos = []

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    db_pontos.append({
        'id': len(db_pontos) + 1, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'), 'mes': agora.strftime('%m'),
        'hora': agora.strftime('%H:%M'), 'geo': f"{lat},{lon}"
    })
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_f = request.args.get('mes', datetime.now().strftime('%m'))
    dias = {}
    for p in [x for x in db_pontos if x['mes'] == mes_f]:
        d = p['data']
        if d not in dias: dias[d] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if p['tipo'] == 'Entrada': 
            dias[d]['e'] = p['hora']; dias[d]['id_e'] = p['id']
        else: 
            dias[d]['s'] = p['hora']; dias[d]['id_s'] = p['id']

    total_m = 0
    dias_completos = 0
    tabela = []

    for data, v in dias.items():
        cor, saldo = "#5a4a4d", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360 # 6h
            total_m += diff
            # LÓGICA DAS CORES
            if diff == 0: cor = "#27ae60" # VERDE
            elif diff > 0: cor = "#2980b9" # AZUL
            else: cor = "#e74c3c" # VERMELHO
            saldo = f"{'+' if diff >= 0 else '-'}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        tabela.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo})

    total_txt = f"{'+' if total_m >= 0 else '-'}{abs(total_m)//60:02d}:{abs(total_m)%60:02d}"
    return render_template('gestao.html', registros=tabela, total=total_txt, contador=dias_completos, mes_atual=mes_f)

@app.route('/excluir/<int:id>')
def excluir(id):
    global db_pontos
    db_pontos = [p for p in db_pontos if p['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))