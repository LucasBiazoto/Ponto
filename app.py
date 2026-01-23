from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz
from math import geodesic # Se der erro no terminal, digite: pip install geopy

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

ADMIN_PASSWORD = "8340"
CLINICA_COORDS = (-23.5233, -46.5330) # Av. Amador Bueno da Veiga, 1230
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
    
    # Lógica de geolocalização
    local_status = "Localização não capturada"
    if lat and lon:
        distancia = geodesic((float(lat), float(lon)), CLINICA_COORDS).meters
        local_status = "Dentro da Empresa" if distancia <= 100 else "Fora da Empresa"

    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': local_status,
        'origem': 'Dispositivo Móvel'
    })
    
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem! 🌸")
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
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    return render_template('gestao.html', registros=registros_ponto)

@app.route('/logout')
def logout():
    session.pop('admin_logado', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)