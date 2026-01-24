from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    registros_ponto.append({
        'id': len(registros_ponto) + 1,
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
    # Esta rota ativa o botão + Manual que estava dando erro 404
    data = request.form.get('data') # formato YYYY-MM-DD
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    
    if data and hora:
        data_formatada = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        registros_ponto.append({
            'id': len(registros_ponto) + 1,
            'nome': "Esther Julia",
            'tipo': tipo,
            'data': data_formatada,
            'hora': hora,
            'local': "Manual"
        })
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Agrupar por data para calcular saldo
    diario = {}
    for r in registros_ponto:
        d = r['data']
        if d not in diario: diario[d] = {'e': None, 's': None, 'id': r['id']}
        if r['tipo'] == 'Entrada': diario[d]['e'] = r['hora']
        else: diario[d]['s'] = r['hora']

    lista_final = []
    total_minutos_extra = 0
    dias_completos = 0

    for data, v in diario.items():
        saldo_texto = "00:00"
        cor = "azul"
        if v['e'] and v['s']:
            dias_completos += 1
            # Cálculo: Saída - Entrada - 6 horas (360 min)
            he, me = map(int, v['e'].split(':'))
            hs, ms = map(int, v['s'].split(':'))
            total_min = (hs * 60 + ms) - (he * 60 + me)
            extra = total_min - 360 # 6h de jornada
            total_minutos_extra += extra
            
            sinal = "+" if extra >= 0 else "-"
            cor = "verde" if extra >= 0 else "vermelho"
            saldo_texto = f"{sinal}{abs(extra)//60:02d}:{abs(extra)%60:02d}"
        
        lista_final.append({'data': data, 'e': v['e'] or '--:--', 's': v['s'] or '--:--', 'saldo': saldo_texto, 'cor': cor, 'id': v['id']})

    sinal_total = "+" if total_minutos_extra >= 0 else "-"
    resumo_total = f"{sinal_total}{abs(total_minutos_extra)//60:02d}:{abs(total_minutos_extra)%60:02d}"

    return render_template('gestao.html', registros=lista_final, total_extra=resumo_total, dias=dias_completos)

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))