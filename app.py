import math

# Coordenadas aproximadas Av. Amador Bueno da Veiga, 1230
LAT_CLINICA = -23.5222
LON_CLINICA = -46.5133

def verificar_local(lat, lon):
    if not lat or not lon: return "GPS Desativado"
    # Cálculo simples de distância (Haversine simplificado)
    dist = math.sqrt((float(lat) - LAT_CLINICA)**2 + (float(lon) - LON_CLINICA)**2)
    return "Na Clínica" if dist < 0.002 else "Fora da Unidade"

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    
    status_local = verificar_local(lat, lon)
    agora = datetime.now(fuso)
    
    registros_ponto.append({
        'id': len(registros_ponto) + 1,
        'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'localizacao': status_local # Informação para a gestão
    })
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    registros_ponto.append({
        'id': len(registros_ponto) + 1,
        'nome': request.form.get('nome'),
        'tipo': request.form.get('tipo'),
        'data': data_br,
        'hora': request.form.get('hora'),
        'localizacao': "Registro Manual" # Identifica que foi feito pela gestão
    })
    return redirect(url_for('gestao'))