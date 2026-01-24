from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'thamiris_clinica_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista global para salvar os pontos (na memória do servidor)
historico = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    historico.append({
        'id': len(historico) + 1,
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
    # Rota que corrige o erro ao salvar ponto manual
    data_input = request.form.get('data')
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    if data_input and hora:
        data_br = datetime.strptime(data_input, '%Y-%m-%d').strftime('%d/%m/%Y')
        historico.append({
            'id': len(historico) + 1, 'nome': "Esther Julia", 
            'tipo': tipo, 'data': data_br, 'hora': hora, 'local': "Manual"
        })
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Lógica para juntar Entrada e Saída na mesma linha (Preenche a tabela do print)
    resumo_diario = {}
    for p in historico:
        dia = p['data']
        if dia not in resumo_diario: resumo_diario[dia] = {'e': '--:--', 's': '--:--', 'id': p['id']}
        if p['tipo'] == 'Entrada': resumo_diario[dia]['e'] = p['hora']
        else: resumo_diario[dia]['s'] = p['hora']

    final_cards = []
    minutos_extras_total = 0
    dias_fechados = 0

    for data, v in resumo_diario.items():
        cor, saldo_txt = "#d68c9a", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_fechados += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            total = (h2 * 60 + m2) - (h1 * 60 + m1)
            extra = total - 360 # Jornada de 6h
            minutos_extras_total += extra
            cor = "#27ae60" if extra >= 0 else "#e74c3c"
            sinal = "+" if extra >= 0 else "-"
            saldo_txt = f"{sinal}{abs(extra)//60:02d}:{abs(extra)%60:02d}"
        
        final_cards.append({'data': data, 'e': v['e'], 's': v['s'], 'saldo': saldo_txt, 'cor': cor, 'id': v['id']})

    resumo_geral = f"{'+' if minutos_extras_total >= 0 else '-'}{abs(minutos_extras_total)//60:02d}:{abs(minutos_extras_total)%60:02d}"
    return render_template('gestao.html', registros=final_cards, total=resumo_geral, dias=dias_fechados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == "8340":
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico
    historico = [p for p in historico if p['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))