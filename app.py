from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import pytz
from geopy.distance import geodesic 

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

ADMIN_PASSWORD = "8340"
CLINICA_COORDS = (-23.5233, -46.5330) 
fuso_horario = pytz.timezone('America/Sao_Paulo')

registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso_horario)
    
    local_status = "N/A"
    if lat and lon and lat != "" and lon != "None":
        try:
            distancia = geodesic((float(lat), float(lon)), CLINICA_COORDS).meters
            local_status = "Dentro da Empresa" if distancia <= 100 else "Fora da Empresa"
        except: pass

    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': local_status,
        'origem': 'Dispositivo Móvel'
    })
    flash(f"Ponto de {tipo} batido! 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': request.form.get('nome'), 'tipo': request.form.get('tipo'),
        'data': data_br, 'hora': request.form.get('hora'),
        'local': 'N/A', 'origem': 'Ação Manual pela Gestão'
    })
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['admin_logado'] = True
        return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Lógica de agrupamento simplificada para evitar Erro 500
    resumo = {}
    for r in registros_ponto:
        dia_nome = (r['data'], r['nome'])
        if dia_nome not in resumo:
            resumo[dia_nome] = {'entrada': '--:--', 'saida': '--:--', 'local': 'N/A', 'id_e': None, 'id_s': None}
        if r['tipo'] == 'Entrada':
            resumo[dia_nome]['entrada'] = r['hora']
            resumo[dia_nome]['id_e'] = r['id']
            resumo[dia_nome]['local'] = r['local']
        else:
            resumo[dia_nome]['saida'] = r['hora']
            resumo[dia_nome]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo = "00:00"
        if v['entrada'] != '--:--' and v['saida'] != '--:--':
            try:
                e = datetime.strptime(v['entrada'], '%H:%M')
                s = datetime.strptime(v['saida'], '%H:%M')
                diff = s - e
                # Cálculo contra 6 horas
                segundos_vivos = diff.total_seconds() - (6 * 3600)
                sinal = "+" if segundos_vivos >= 0 else "-"
                abs_sec = abs(segundos_vivos)
                hh, mm = int(abs_sec // 3600), int((abs_sec % 3600) // 60)
                saldo = f"{sinal}{hh:02d}:{mm:02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'entrada': v['entrada'], 
            'saida': v['saida'], 'saldo': saldo, 'local': v['local'],
            'id_e': v['id_e'], 'id_s': v['id_s']
        })
    
    return render_template('gestao.html', registros=dados_finais)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)