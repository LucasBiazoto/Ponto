from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# IMPORTANTE: Para não perder dados, o Lucas deve conectar aqui um Banco de Dados.
# Por enquanto, manteremos a lista, mas ele deve usar SQL para persistência real.
historico_db = [] 

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat') # Geolocalização enviada pelo navegador
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    
    historico_db.append({
        'id': len(historico_db) + 1,
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'mes': agora.strftime('%m'), # Para o filtro de meses
        'hora': agora.strftime('%H:%M'),
        'geo': f"{lat}, {lon}" if lat else "Sem GPS"
    })
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_selecionado = request.args.get('mes', datetime.now().strftime('%m'))
    
    # Agrupamento Inteligente por Dia
    dias = {}
    for p in [x for x in historico_db if x['mes'] == mes_selecionado]:
        d = p['data']
        if d not in dias: dias[d] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if p['tipo'] == 'Entrada': 
            dias[d]['e'] = p['hora']
            dias[d]['id_e'] = p['id']
        else: 
            dias[d]['s'] = p['hora']
            dias[d]['id_s'] = p['id']

    total_minutos_extra = 0
    contagem_dias_completos = 0
    tabela_final = []

    for data, v in dias.items():
        cor, saldo_txt = "#5a4a4d", "00:00" # Cinza padrão
        
        # SÓ SOMA E CALCULA SE TIVER ENTRADA E SAÍDA
        if v['e'] != '--:--' and v['s'] != '--:--':
            contagem_dias_completos += 1
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            total = (h2 * 60 + m2) - (h1 * 60 + m1)
            diff = total - 360 # 6 horas de jornada
            total_minutos_extra += diff
            
            # LÓGICA DE CORES TRIPLE
            if diff == 0: cor = "#27ae60" # VERDE (6h cravadas)
            elif diff > 0: cor = "#2980b9" # AZUL (Extra)
            else: cor = "#e74c3c" # VERMELHO (Débito)
            
            sinal = "+" if diff >= 0 else "-"
            saldo_txt = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        tabela_final.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo_txt})

    total_final = f"{'+' if total_minutos_extra >= 0 else '-'}{abs(total_minutos_extra)//60:02d}:{abs(total_minutos_extra)%60:02d}"
    return render_template('gestao.html', registros=tabela_final, total=total_final, contador=contagem_dias_completos, mes=mes_selecionado)