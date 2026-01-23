@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    resumo = {}
    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None, 'loc': 'N/A'}
        
        if r['tipo'] == 'Entrada':
            resumo[chave]['e'] = r['hora']
            resumo[chave]['id_e'] = r['id']
            resumo[chave]['loc'] = r.get('local', 'N/A') # Recupera a localização
        else:
            resumo[chave]['s'] = r['hora']
            resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo_str = "00:00"
        status_dia = "normal" # Define a cor padrão (Azul)
        
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                total_minutos = (h2 * 60 + m2) - (h1 * 60 + m1)
                
                saldo_minutos = total_minutos - 360 # Base 6h
                
                if saldo_minutos > 0: status_dia = "extra"
                elif saldo_minutos < 0: status_dia = "atraso"
                
                sinal = "+" if saldo_minutos >= 0 else "-"
                abs_min = abs(saldo_minutos)
                saldo_str = f"{sinal}{abs_min // 60:02d}:{abs_min % 60:02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'],
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo_str, 
            'loc': v['loc'], 'status': status_dia
        })
    
    return render_template('gestao.html', registros=dados_finais)