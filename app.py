from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# NOTA PARA O LUCAS: Para persistência real (dados não sumirem), 
# use o Vercel Postgres ou conecte ao Supabase aqui.
historico_db = [] 

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    
    historico_db.append({
        'id': len(historico_db) + 1,
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'mes': agora.strftime('%m'),
        'hora': agora.strftime('%H:%M'),
        'geo': f"{lat},{lon}" if lat else "GPS Off"
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/add_manual', methods=['POST'])
def add_manual():
    data_cal = request.form.get('data')
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    if data_cal and hora:
        data_br = datetime.strptime(data_cal, '%Y-%m-%d').strftime('%d/%m/%Y')
        mes_br = datetime.strptime(data_cal, '%Y-%m-%d').strftime('%m')
        historico_db.append({
            'id': len(historico_db) + 1, 'tipo': tipo, 'data': data_br, 
            'mes': mes_br, 'hora': hora, 'geo': "Manual"
        })
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico_db
    historico_db = [p for p in historico_db if p['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    # Agrupamento por dia
    diario = {}
    for p in [x for x in historico_db if x['mes'] == mes_f]:
        d = p['data']
        if d not in diario: diario[d] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if p['tipo'] == 'Entrada': 
            diario[d]['e'] = p['hora']; diario[d]['id_e'] = p['id']
        else: 
            diario[d]['s'] = p['hora']; diario[d]['id_s'] = p['id']

    total_m = 0
    dias_count = 0
    tabela = []

    for data, v in diario.items():
        cor, saldo = "#5a4a4d", "00:00"
        # SÓ SOMA SE TIVER OS DOIS NO MESMO DIA
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_count += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360 # Jornada 6h
            total_m += diff
            
            if diff == 0: cor = "#27ae60"    # VERDE
            elif diff > 0: cor = "#2980b9"  # AZUL
            else: cor = "#e74c3c"           # VERMELHO
            
            sinal = "+" if diff >= 0 else "-"
            saldo = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        tabela.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo})

    total_txt = f"{'+' if total_m >= 0 else '-'}{abs(total_m)//60:02d}:{abs(total_m)%60:02d}"
    return render_template('gestao.html', registros=tabela, total=total_txt, contador=dias_count, mes_atual=mes_f)