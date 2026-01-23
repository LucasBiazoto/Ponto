@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    resumo = {}
    # Agrupa por data e nome
    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in resumo:
            resumo[chave] = {'entrada': '--:--', 'saida': '--:--', 'id_e': None, 'id_s': None, 'local': 'N/A'}
        
        if r['tipo'] == 'Entrada':
            resumo[chave]['entrada'] = r['hora']
            resumo[chave]['id_e'] = r['id']
            resumo[chave]['local'] = r['local']
        else:
            resumo[chave]['saida'] = r['hora']
            resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo_str = "00:00"
        # Só tenta calcular se houver Entrada E Saída
        if v['entrada'] != '--:--' and v['saida'] != '--:--':
            try:
                # Converte para minutos para facilitar a conta
                h1, m1 = map(int, v['entrada'].split(':'))
                h2, m2 = map(int, v['saida'].split(':'))
                total_minutos = (h2 * 60 + m2) - (h1 * 60 + m1)
                
                # Diferença contra a base de 6 horas (360min)
                saldo_minutos = total_minutos - 360
                sinal = "+" if saldo_minutos >= 0 else "-"
                abs_min = abs(saldo_minutos)
                saldo_str = f"{sinal}{abs_min // 60:02d}:{abs_min % 60:02d}"
            except:
                saldo_str = "Erro"

        dados_finais.append({
            'data': data, 'nome': nome, 'entrada': v['entrada'],
            'saida': v['saida'], 'id_e': v['id_e'], 'id_s': v['id_s'],
            'saldo': saldo_str, 'local': v['local']
        })
    
    return render_template('gestao.html', registros=dados_finais)