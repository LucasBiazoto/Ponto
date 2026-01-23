from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz
import math

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_permanente_key'
fuso = pytz.timezone('America/Sao_Paulo')

# Coordenadas Unidade Penha
LAT_CLINICA = -23.5222
LON_CLINICA = -46.5133

def calcular_localizacao(lat, lon):
    if not lat or not lon or lat == "" or lon == "":
        return "GPS desligado"
    try:
        dist = math.sqrt((float(lat) - LAT_CLINICA)**2 + (float(lon) - LON_CLINICA)**2)
        return "Na Clínica" if dist < 0.002 else "Fora da Unidade"
    except:
        return "Erro Localização"

registros_ponto = []

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = "Esther Julia"
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    
    agora = datetime.now(fuso)
    registros_ponto.append({
        'id': len(registros_ponto) + 1,
        'nome': nome,
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': calcular_localizacao(lat, lon)
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    try:
        data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
        registros_ponto.append({
            'id': len(registros_ponto) + 1,
            'nome': "Esther Julia",
            'tipo': request.form.get('tipo'),
            'data': data_br,
            'hora': request.form.get('hora'),
            'local': "Registro Manual"
        })
    except: pass
    return redirect(url_for('gestao'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    resumo = {}
    total_minutos = 0
    dias_completos = 0

    # Agrupar registros por dia
    for r in registros_ponto:
        if r['data'].split('/')[1] == mes_sel:
            chave = r['data']
            if chave not in resumo:
                resumo[chave] = {'e': '--:--', 's': '--:--', 'local': r['local'], 'id': r['id']}
            if r['tipo'] == 'Entrada': resumo[chave]['e'] = r['hora']
            else: resumo[chave]['s'] = r['hora']

    # Calcular saldos e dias (Somente se houver entrada E saída)
    dados_finais = []
    for data, v in resumo.items():
        cor, saldo = "azul", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
            total_minutos += diff
            saldo = f"{'+' if diff >= 0 else '-'}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
            cor = "verde" if diff >= 0 else "vermelho"
        
        dados_finais.append({'data': data, 'e': v['e'], 's': v['s'], 'local': v['local'], 'saldo': saldo, 'cor': cor, 'id': v['id']})

    s_total = f"{'+' if total_minutos >= 0 else '-'}{abs(total_minutos)//60:02d}:{abs(total_minutos)%60:02d}"
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, mes_sel=mes_sel, qtd_dias=dias_completos)