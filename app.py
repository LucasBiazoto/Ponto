from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista de registros brutos
historico_bruto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    historico_bruto.append({
        'id': len(historico_bruto) + 1,
        'colaboradora': "Esther Julia",
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': "Na Clínica"
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/add_manual', methods=['POST'])
def add_manual():
    data = request.form.get('data') # formato YYYY-MM-DD
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    if data and hora:
        data_f = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        historico_bruto.append({
            'id': len(historico_bruto) + 1,
            'colaboradora': "Esther Julia",
            'tipo': tipo,
            'data': data_f,
            'hora': hora,
            'local': "Manual"
        })
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # ORGANIZAÇÃO POR DIA (Para preencher as colunas do seu print)
    diario = {}
    for r in historico_bruto:
        dia = r['data']
        if dia not in diario: diario[dia] = {'e': '--:--', 's': '--:--', 'id': r['id']}
        if r['tipo'] == 'Entrada': diario[dia]['e'] = r['hora']
        else: diario[dia]['s'] = r['hora']

    registros_processados = []
    total_minutos_extra = 0
    dias_trabalhados = 0

    for data, v in diario.items():
        saldo = "00:00"
        cor = "#d68c9a" # Cor padrão rosa
        
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_trabalhados += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            minutos_total = (h2 * 60 + m2) - (h1 * 60 + m1)
            extra = minutos_total - 360 # Jornada de 6h
            total_minutos_extra += extra
            
            sinal = "+" if extra >= 0 else "-"
            cor = "#27ae60" if extra >= 0 else "#e74c3c" # Verde ou Vermelho
            saldo = f"{sinal}{abs(extra)//60:02d}:{abs(extra)%60:02d}"
            
        registros_processados.append({
            'data': data, 'e': v['e'], 's': v['s'], 
            'saldo': saldo, 'cor': cor, 'id': v['id']
        })

    s_total = "+" if total_minutos_extra >= 0 else "-"
    total_final = f"{s_total}{abs(total_minutos_extra)//60:02d}:{abs(total_minutos_extra)%60:02d}"

    return render_template('gestao.html', registros=registros_processados, total_horas=total_final, dias=dias_trabalhados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == "8340":
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico_bruto
    historico_bruto = [r for r in historico_bruto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))