@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Dicionário para agrupar Entrada e Saída na mesma linha
    resumo = {}
    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'e': '--:--', 's': '--:--', 'loc': 'N/A', 'id_e': None, 'id_s': None}
        
        if r['tipo'] == 'Entrada':
            resumo[chave]['e'] = r['hora']
            resumo[chave]['id_e'] = r['id']
            resumo[chave]['loc'] = r['local']
        else:
            resumo[chave]['s'] = r['hora']
            resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo = "00:00"
        # Só calcula se houver os dois horários
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                formato = '%H:%M'
                diff = datetime.strptime(v['s'], formato) - datetime.strptime(v['e'], formato)
                # Cálculo base 6 horas
                segundos = diff.total_seconds() - (6 * 3600)
                sinal = "+" if segundos >= 0 else "-"
                abs_sec = abs(segundos)
                saldo = f"{sinal}{int(abs_sec//3600):02d}:{int((abs_sec%3600)//60):02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'entrada': v['e'], 'saida': v['s'],
            'saldo': saldo, 'local': v['loc'], 'id_e': v['id_e'], 'id_s': v['id_s']
        })
    
    return render_template('gestao.html', registros=dados_finais)