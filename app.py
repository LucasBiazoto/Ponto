from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'
ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')

# Base de dados temporária
registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    agora = datetime.now(fuso_horario)
    mes_sel = request.args.get('mes', agora.strftime('%m'))
    ano_sel = request.args.get('ano', agora.strftime('%Y'))
    
    resumo = {}
    total_minutos_periodo = 0

    for r in registros_ponto:
        r_data = datetime.strptime(r['data'], '%d/%m/%Y')
        if r_data.strftime('%m') == mes_sel and r_data.strftime('%Y') == ano_sel:
            chave = (r['data'], r['nome'])
            if chave not in resumo:
                resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None, 'loc': 'N/A'}
            
            if r['tipo'] == 'Entrada':
                resumo[chave]['e'] = r['hora']
                resumo[chave]['id_e'] = r['id']
                resumo[chave]['loc'] = r.get('local', 'Unidade Penha')
            else:
                resumo[chave]['s'] = r['hora']
                resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo_str, cor_status = "00:00", "azul"
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360 # Base 6h
                total_minutos_periodo += diff
                
                if diff > 0: cor_status = "verde"
                elif diff < 0: cor_status = "vermelho"
                
                sinal = "+" if diff >= 0 else "-"
                abs_m = abs(diff)
                saldo_str = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'],
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo_str, 
            'loc': v['loc'], 'cor': cor_status
        })

    sinal_t = "+" if total_minutos_periodo >= 0 else "-"
    abs_t = abs(total_minutos_periodo)
    soma_total = f"{sinal_t}{abs_t//60:02d}:{abs_t%60:02d}"

    return render_template('gestao.html', registros=dados_finais, soma_total=soma_total, mes_sel=mes_sel, ano_sel=ano_sel)

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    loc = request.form.get('local_status') or "Unidade Penha"
    agora = datetime.now(fuso_horario)
    registros_ponto.append({
        'id': len(registros_ponto), 'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'), 'hora': agora.strftime('%H:%M'), 'local': loc
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem! 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_sel = request.form.get('data')
    data_br = datetime.strptime(data_sel, '%Y-%m-%d').strftime('%d/%m/%Y')
    registros_ponto.append({
        'id': len(registros_ponto), 'nome': request.form.get('nome'), 
        'tipo': request.form.get('tipo'), 'data': data_br, 
        'hora': request.form.get('hora'), 'local': 'Manual pela Gestão'
    })
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

if __name__ == '__main__':
    app.run(debug=True)