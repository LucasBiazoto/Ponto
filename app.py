from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

# Configurações fixas
ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')
registros_ponto = [] # Armazenamento temporário

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso_horario)
    
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': nome, 
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': 'Verificado'
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem! 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_sel = request.form.get('data')
    data_br = datetime.strptime(data_sel, '%Y-%m-%d').strftime('%d/%m/%Y')
    
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': request.form.get('nome'), 
        'tipo': request.form.get('tipo'),
        'data': data_br, 
        'hora': request.form.get('hora'),
        'local': 'Manual'
    })
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Agrupamento Seguro para evitar Erro 500
    resumo = {}
    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        
        if r['tipo'] == 'Entrada':
            resumo[chave]['e'] = r['hora']
            resumo[chave]['id_e'] = r['id']
        else:
            resumo[chave]['s'] = r['hora']
            resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo = "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                # Cálculo simples em minutos
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1)
                # Base 6 horas (360 min)
                s_min = diff - 360
                sinal = "+" if s_min >= 0 else "-"
                abs_m = abs(s_min)
                saldo = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'],
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo
        })
    
    return render_template('gestao.html', registros=dados_finais)

@app.route('/logout')
def logout():
    session.clear() # Limpa tudo para evitar erro na sessão
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)