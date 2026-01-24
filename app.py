from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# IMPORTANTE: Lucas, para os dados não sumirem, use um banco de dados (SQL ou Supabase).
# Esta lista é temporária e apaga quando o Vercel reinicia.
historico_permanente = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    
    historico_permanente.append({
        'id': len(historico_permanente) + 1,
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'mes': agora.strftime('%m'),
        'hora': agora.strftime('%H:%M'),
        'geo': f"{lat}, {lon}" if lat else "Sem GPS"
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_filtro = request.args.get('mes', datetime.now().strftime('%m'))
    
    # Agrupar Entrada e Saída por dia
    dias = {}
    for p in [x for x in historico_permanente if x['mes'] == mes_filtro]:
        d = p['data']
        if d not in dias: dias[d] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if p['tipo'] == 'Entrada': 
            dias[d]['e'] = p['hora']; dias[d]['id_e'] = p['id']
        else: 
            dias[d]['s'] = p['hora']; dias[d]['id_s'] = p['id']

    total_minutos_geral = 0
    contagem_dias = 0
    lista_tabela = []

    for data, v in dias.items():
        cor, saldo_str = "#5a4a4d", "00:00"
        
        # SÓ SOMA SE HOUVER ENTRADA E SAÍDA NO MESMO DIA
        if v['e'] != '--:--' and v['s'] != '--:--':
            contagem_dias += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            total_min = (h2 * 60 + m2) - (h1 * 60 + m1)
            diff = total_min - 360 # Jornada de 6h
            total_minutos_geral += diff
            
            # LÓGICA DE CORES
            if diff == 0: cor = "#27ae60" # VERDE
            elif diff > 0: cor = "#2980b9" # AZUL
            else: cor = "#e74c3c" # VERMELHO
            
            sinal = "+" if diff >= 0 else "-"
            saldo_str = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        lista_tabela.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo_str})

    resumo_total = f"{'+' if total_minutos_extra >= 0 else '-'}{abs(total_minutos_extra)//60:02d}:{abs(total_minutos_extra)%60:02d}"
    return render_template('gestao.html', registros=lista_tabela, total=resumo_total, contador=contagem_dias, mes_atual=mes_filtro)

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico_permanente
    historico_permanente = [p for p in historico_permanente if p['id'] != id]
    return redirect(url_for('gestao'))

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