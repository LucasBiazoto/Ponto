from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz
from geopy.distance import geodesic

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
fuso = pytz.timezone('America/Sao_Paulo')

# Coordenadas da Clínica (Exemplo: Penha)
COORD_CLINICA = (-23.5222, -46.5133)

registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    agora = datetime.now(fuso)
    
    localizacao = "GPS Desligado"
    if lat and lon:
        dist = geodesic((float(lat), float(lon)), COORD_CLINICA).meters
        localizacao = "Na Clínica" if dist < 200 else "Fora da Unidade"

    registros_ponto.append({
        'id': len(registros_ponto) + 1,
        'nome': "Esther Julia",
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': localizacao
    })
    
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    return render_template('gestao.html', registros=registros_ponto)

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros_ponto
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
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