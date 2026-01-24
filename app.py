from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista para armazenar os pontos
historico_pontos = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    historico_pontos.append({
        'id': len(historico_pontos) + 1,
        'nome': "Esther Julia",
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': "Na Clínica"
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/add_manual', methods=['POST'])
def add_manual():
    # Rota que resolve o erro ao clicar em 'Salvar' no Manual
    data_cal = request.form.get('data')
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    if data_cal and hora:
        data_br = datetime.strptime(data_cal, '%Y-%m-%d').strftime('%d/%m/%Y')
        historico_pontos.append({
            'id': len(historico_pontos) + 1,
            'nome': "Esther Julia",
            'tipo': tipo,
            'data': data_br,
            'hora': hora,
            'local': "Manual"
        })
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Organiza os pontos por dia para preencher Entrada/Saída na mesma linha
    organizado = {}
    for p in historico_pontos:
        d = p['data']
        if d not in organizado: organizado[d] = {'e': '--:--', 's': '--:--', 'id': p['id']}
        if p['tipo'] == 'Entrada': organizado[d]['e'] = p['hora']
        else: organizado[d]['s'] = p['hora']

    lista_final = []
    total_minutos_extra = 0
    dias_count = 0

    for data, v in organizado.items():
        cor, saldo = "#d68c9a", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_count += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            total_trabalhado = (h2 * 60 + m2) - (h1 * 60 + m1)
            extra = total_trabalhado - 360 # Jornada de 6h
            total_minutos_extra += extra
            
            cor = "#27ae60" if extra >= 0 else "#e74c3c"
            sinal = "+" if extra >= 0 else "-"
            saldo = f"{sinal}{abs(extra)//60:02d}:{abs(extra)%60:02d}"
        
        lista_final.append({'data': data, 'e': v['e'], 's': v['s'], 'saldo': saldo, 'cor': cor, 'id': v['id']})

    resumo_total = f"{'+' if total_minutos_extra >= 0 else '-'}{abs(total_minutos_extra)//60:02d}:{abs(total_minutos_extra)%60:02d}"
    return render_template('gestao.html', registros=lista_final, total_extra=resumo_total, qtd_dias=dias_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == "8340":
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico_pontos
    historico_pontos = [p for p in historico_pontos if p['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))