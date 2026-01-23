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
        'id': len(registros_ponto),
        'nome': nome, 
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': 'Unidade Penha'
    })
    
    # MENSAGENS QUE VOCÊ PEDIU
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "8340":
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    resumo = {}
    total_minutos_saldo = 0

    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        
        if r['tipo'] == 'Entrada':
            resumo[chave]['e'] = r['hora']; resumo[chave]['id_e'] = r['id']
        else:
            resumo[chave]['s'] = r['hora']; resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo_str, cor = "00:00", "azul"
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
                total_minutos_saldo += diff
                cor = "verde" if diff > 0 else "vermelho" if diff < 0 else "azul"
                sinal = "+" if diff >= 0 else "-"
                abs_m = abs(diff)
                saldo_str = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            except: pass
            
        dados_finais.append({'data': data, 'nome': nome, 'e': v['e'], 's': v['s'], 'saldo': saldo_str, 'cor': cor})

    s_total = f"{'+' if total_minutos_saldo >= 0 else '-'}{abs(total_minutos_periodo)//60:02d}:{abs(total_minutos_periodo)%60:02d}" if 'total_minutos_periodo' in locals() else "+00:00"
    
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, mes_sel=mes_sel)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)