@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    resumo = {}
    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'entrada': '--:--', 'saida': '--:--', 'local': 'N/A', 'id_e': None, 'id_s': None}
        
        if r['tipo'] == 'Entrada':
            resumo[chave]['entrada'] = r['hora']
            resumo[chave]['id_e'] = r['id']
            resumo[chave]['local'] = r['local']
        elif r['tipo'] == 'Saída':
            resumo[chave]['saida'] = r['hora']
            resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo = "00:00"
        if v['entrada'] != '--:--' and v['saida'] != '--:--':
            try:
                e = datetime.strptime(v['entrada'], '%H:%M')
                s = datetime.strptime(v['saida'], '%H:%M')
                diff = s - e
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