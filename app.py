from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret_key'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista temporária de registros
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
        'nome': nome,
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': 'Unidade Penha'
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    data_input = request.form.get('data') # Vem no formato YYYY-MM-DD
    data_br = datetime.strptime(data_input, '%Y-%m-%d').strftime('%d/%m/%Y')
    
    registros_ponto.append({
        'id': len(registros_ponto) + 1,
        'nome': request.form.get('nome'),
        'tipo': request.form.get('tipo'),
        'data': data_br,
        'hora': request.form.get('hora'),
        'local': 'Manual pela Gestão'
    })
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    if not session.get('admin_logado'): return redirect(url_for('login'))
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == "8340":
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
        else:
            flash("Senha incorreta!")
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    resumo = {}
    total_minutos_periodo = 0

    for r in registros_ponto:
        if r['data'].split('/')[1] == mes_sel:
            chave = (r['data'], r['nome'])
            if chave not in resumo:
                resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None, 'loc': r.get('local', 'N/A')}
            
            if r['tipo'] == 'Entrada':
                resumo[chave]['e'] = r['hora']
                resumo[chave]['id_e'] = r['id']
            else:
                resumo[chave]['s'] = r['hora']
                resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        cor, saldo_str = "azul", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
                total_minutos_periodo += diff
                cor = "verde" if diff > 0 else "vermelho" if diff < 0 else "azul"
                sinal = "+" if diff >= 0 else "-"
                abs_m = abs(diff)
                saldo_str = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'], 
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo_str, 'cor': cor, 'loc': v['loc']
        })

    s_total = f"{'+' if total_minutos_periodo >= 0 else '-'}{abs(total_minutos_periodo)//60:02d}:{abs(total_minutos_periodo)%60:02d}"
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, mes_sel=mes_sel)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)