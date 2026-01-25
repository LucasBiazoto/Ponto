@app.route('/exportar_pdf')
def exportar_pdf():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT data, tipo, hora FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close()
    conn.close()

    # Mesma lógica de agrupamento do painel
    dias = {}
    for r in registros_raw:
        data, tipo, hora = r
        if data not in dias: dias[data] = {'entrada': '--:--', 'saida': '--:--'}
        if tipo == 'Entrada': dias[data]['entrada'] = hora
        else: dias[data]['saida'] = hora

    # Configuração do PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho Estilizado
    pdf.set_text_color(214, 140, 154) # Rosa Dra. Thamiris
    pdf.set_font("Arial", "B", 20)
    pdf.cell(190, 15, "Dra. Thamiris Araujo", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 5, "Estetica Avancada - Relatorio de Frequencia", ln=True, align="C")
    pdf.ln(10)
    
    # Info do Mês
    pdf.set_text_color(90, 74, 77) # Cor do texto padrão
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"Periodo: Mes {mes_f} / 2026", ln=True, align="L")
    pdf.ln(5)

    # Tabela - Cabeçalho
    pdf.set_fill_color(252, 228, 236) # Fundo Rosa Claro
    pdf.set_font("Arial", "B", 10)
    pdf.cell(45, 10, " Data", 1, 0, 'L', True)
    pdf.cell(45, 10, " Entrada", 1, 0, 'L', True)
    pdf.cell(45, 10, " Saida", 1, 0, 'L', True)
    pdf.cell(55, 10, " Saldo Diário (Meta 6h)", 1, 1, 'L', True)

    # Tabela - Dados
    pdf.set_font("Arial", "", 10)
    total_segundos = 0
    dias_count = 0
    
    for data in sorted(dias.keys()):
        info = dias[data]
        saldo_txt = "0.0h"
        
        if info['entrada'] != '--:--' and info['saida'] != '--:--':
            dias_count += 1
            t1 = datetime.strptime(info['entrada'], '%H:%M')
            t2 = datetime.strptime(info['saida'], '%H:%M')
            horas = (t2 - t1).total_seconds() / 3600
            saldo = horas - 6
            total_segundos += (t2 - t1).total_seconds()
            saldo_txt = f"{saldo:+.1f}h"

        pdf.cell(45, 10, f" {data}", 1)
        pdf.cell(45, 10, f" {info['entrada']}", 1)
        pdf.cell(45, 10, f" {info['saida']}", 1)
        pdf.cell(55, 10, f" {saldo_txt}", 1, 1)

    # Resumo Final
    pdf.ln(10)
    total_h = total_segundos / 3600
    saldo_geral = total_h - (dias_count * 6)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 8, f"Dias Trabalhados: {dias_count}", ln=True)
    pdf.cell(190, 8, f"Saldo Total de Horas Extras: {saldo_geral:+.1f}h", ln=True)
    
    # Rodapé do PDF
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(190, 10, "Desenvolvido por Lucas Biazoto - Sistema de Gestao Dra. Thamiris Araujo", 0, 0, 'C')

    res = make_response(pdf.output(dest='S').encode('latin-1', 'ignore'))
    res.headers.set('Content-Disposition', 'attachment', filename=f'Relatorio_{mes_f}_Thamiris.pdf')
    res.headers.set('Content-Type', 'application/pdf')
    return res