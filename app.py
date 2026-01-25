from math import radians, cos, sin, asin, sqrt

# Coordenadas da Clínica (Aprox. Amador Bueno da Veiga, 1230)
CLINICA_LAT = -23.5218
CLINICA_LON = -46.5428

def calcular_distancia(lat1, lon1):
    # Raio da Terra em km
    r = 6371
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), CLINICA_LAT, CLINICA_LON])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return (c * r) * 1000 # Retorna em metros

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    tipo = request.form.get('tipo')
    lat = request.form.get('lat') or '0'
    lon = request.form.get('lon') or '0'
    
    # Verifica geolocalização
    status_geo = "Fora da Empresa"
    if lat != '0':
        distancia = calcular_distancia(lat, lon)
        if distancia <= 100: # 100 metros de tolerância
            status_geo = "Dentro da Empresa"
    
    agora = datetime.now(fuso)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO pontos (tipo, data, mes, hora, geo) VALUES (%s, %s, %s, %s, %s)',
                (tipo, agora.strftime('%d/%m/%Y'), agora.strftime('%m'), agora.strftime('%H:%M'), status_geo))
    conn.commit()
    cur.close()
    conn.close()
    
    flash("Bom trabalho meu bem 🌸" if tipo == 'Entrada' else "Bom descanso meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/exportar_pdf')
def exportar_pdf():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    # Aqui pegamos os dados processados para incluir o saldo no PDF
    # (Reutilize a lógica de cálculo do saldo que já temos na rota /gestao)
    # ... [Lógica de processamento de registros para o PDF] ...

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, f"RELATORIO COMPLETO - MES {mes_f}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, "Clinica Dra Thamiris Araujo - Estetica Avancada", ln=True, align="C")
    pdf.ln(5)

    # Cabeçalho
    pdf.set_fill_color(214, 140, 154) # Cor Rosa da clínica
    pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 10, "Data", 1, 0, 'C', True)
    pdf.cell(30, 10, "Entrada", 1, 0, 'C', True)
    pdf.cell(30, 10, "Saida", 1, 0, 'C', True)
    pdf.cell(35, 10, "Saldo (6h)", 1, 0, 'C', True)
    pdf.cell(60, 10, "Localizacao", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    # Loop de registros (usando os dados processados da tabela de gestão)
    # pdf.cell(...)
    
    response = make_response(pdf.output(dest='S').encode('latin-1', 'ignore'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'Relatorio_Completo_Mes_{mes_f}.pdf')
    return response