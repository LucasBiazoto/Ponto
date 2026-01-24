from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import pytz
import io

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Base de dados em memória
historico = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    
    local = "GPS Desligado"
    if lat and lon:
        # Lógica simplificada de geolocalização (exemplo)
        local = "Na Unidade" if "-23.5" in str(lat) else "Fora da Unidade"

    historico.append({
        'id': len(historico) + 1,
        'nome': "Esther Julia",
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'mes': agora.strftime('%b'),
        'hora': agora.strftime('%H:%M'),
        'local': local
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    mes_filtro = request.args.get('mes', 'Jan')
    
    # Agrupar por dia para lógica de cores
    diario = {}
    for p in [x for x in historico if x['mes'] == mes_filtro]:
        d = p['data']
        if d not in diario: diario[d] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if p['tipo'] == 'Entrada': 
            diario[d]['e'] = p['hora']
            diario[d]['id_e'] = p['id']
        else: 
            diario[d]['s'] = p['hora']
            diario[d]['id_s'] = p['id']

    final = []
    total_minutos = 0
    for data, v in diario.items():
        cor = "gray"
        saldo = "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            minutos = (h2 * 60 + m2) - (h1 * 60 + m1)
            diff = minutos - 360 # 6 horas
            total_minutos += diff
            
            # LÓGICA DAS CORES SOLICITADA
            if diff == 0: cor = "#27ae60" # VERDE (6h exatas)
            elif diff > 0: cor = "#2980b9" # AZUL (Extra)
            else: cor = "#e74c3c" # VERMELHO (Débito)
            
            sinal = "+" if diff >= 0 else "-"
            saldo = f"{sinal}{abs(diff)//60:02d}:{abs(diff)%60:02d}"
        
        final.append({'data': data, 'e': v['e'], 's': v['s'], 'id_e': v['id_e'], 'id_s': v['id_s'], 'cor': cor, 'saldo': saldo})

    total_txt = f"{'+' if total_minutos >= 0 else '-'}{abs(total_minutos)//60:02d}:{abs(total_minutos)%60:02d}"
    return render_template('gestao.html', registros=final, total=total_txt, dias=len(final), mes_atual=mes_filtro)

@app.route('/excluir/<int:id>')
def excluir(id):
    global historico
    historico = [p for p in historico if p['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/exportar_pdf')
def exportar_pdf():
    # Simulação de geração de PDF (Envia arquivo de texto para exemplo)
    output = io.BytesIO()
    output.write(b"Relatorio de Pontos - Esther Julia\n")
    output.seek(0)
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='ponto_esther.pdf')

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