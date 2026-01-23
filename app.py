from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz
from geopy.distance import geodesic # Motor de cálculo de distância

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

# --- CONFIGURAÇÕES DA DRA. THAMIRIS ---
ADMIN_PASSWORD = "8340"
# Coordenadas exatas da Av. Amador Bueno da Veiga, 1230
CLINICA_COORDS = (-23.5233, -46.5330) 
fuso_horario = pytz.timezone('America/Sao_Paulo')

# Armazenamento temporário dos registros
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
    hora_limpa = agora.strftime('%H:%M')
    data_limpa = agora.strftime('%d/%m/%Y')
    
    local_status = "Localização não capturada"
    
    # Lógica de Geolocalização com proteção contra erros
    if lat and lon and lat != "None" and lon != "None":
        try:
            ponto_colaboradora = (float(lat), float(lon))
            distancia = geodesic(ponto_colaboradora, CLINICA_COORDS).meters
            # Raio de 100 metros de tolerância
            local_status = "Dentro da Empresa" if distancia <= 100 else "Fora da Empresa"
        except:
            local_status = "Erro na geolocalização"

    # Salva o registro na lista
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': nome, 
        'tipo': tipo,
        'data': data_limpa,
        'hora': hora_limpa,
        'local': local_status,
        'origem': 'Dispositivo Móvel'
    })
    
    msg = "Bom trabalho meu bem! 🌸" if tipo == 'Entrada' else "Bom descanso meu bem! 🌸"
    flash(f"{msg} Ponto batido às {hora_limpa}")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): 
        return redirect(url_for('login'))
        
    data_input = request.form.get('data')
    hora = request.form.get('hora')
    nome = request.form.get('nome')
    tipo = request.form.get('tipo')
    
    # Formata a data vinda do calendário do navegador
    data_br = datetime.strptime(data_input, '%Y-%m-%d').strftime('%d/%m/%Y')
    
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': nome, 
        'tipo': tipo,
        'data': data_br, 
        'hora': hora,
        'local': 'N/A', 
        'origem': 'Ação Manual pela Gestão'
    })
    
    flash("Registro manual inserido com sucesso! ✨")
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:id>')
def excluir(id):
    if not session.get('admin_logado'):
        return redirect(url_for('login'))
        
    global registros_ponto
    # Filtra a lista removendo apenas o item com o ID clicado
    registros_ponto = [r for r in registros_ponto if r['id'] != id]
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('password')
        if senha == ADMIN_PASSWORD:
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
        flash("Senha incorreta, tente novamente.")
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'):
        return redirect(url_for('login'))
    return render_template('gestao.html', registros=registros_ponto)

@app.route('/logout')
def logout():
    session.pop('admin_logado', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)