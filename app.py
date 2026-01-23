from datetime import datetime, timedelta

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'):
        return redirect(url_for('login'))
    
    # Organizar batidas por data e nome para calcular o saldo
    processados = []
    batidas_por_dia = {}

    for r in registros_ponto:
        chave = (r['data'], r['nome'])
        if chave not in batidas_por_dia:
            batidas_por_dia[chave] = {'Entrada': None, 'Saída': None, 'local': r['local'], 'origem': r['origem'], 'id_entrada': None, 'id_saida': None}
        
        if r['tipo'] == 'Entrada':
            batidas_por_dia[chave]['Entrada'] = r['hora']
            batidas_por_dia[chave]['id_entrada'] = r['id']
        else:
            batidas_por_dia[chave]['Saída'] = r['hora']
            batidas_por_dia[chave]['id_saida'] = r['id']

    for (data, nome), horas in batidas_por_dia.items():
        saldo_texto = "Pendente"
        if horas['Entrada'] and horas['Saída']:
            # Cálculo da diferença
            formato = '%H:%M'
            t1 = datetime.strptime(horas['Entrada'], formato)
            t2 = datetime.strptime(horas['Saída'], formato)
            diferenca = t2 - t1
            
            # Jornada de 6 horas
            jornada_6h = timedelta(hours=6)
            saldo = diferenca - jornada_6h
            
            # Formatação do saldo (positivo ou negativo)
            total_segundos = int(saldo.total_seconds())
            sinal = "+" if total_segundos >= 0 else "-"
            abs_segundos = abs(total_segundos)
            hh, rem = divmod(abs_segundos, 3600)
            mm, _ = divmod(rem, 60)
            saldo_texto = f"{sinal}{hh:02d}:{mm:02d}"

        processados.append({
            'data': data, 'nome': nome,
            'entrada': horas['Entrada'] or "--:--",
            'saida': horas['Saída'] or "--:--",
            'saldo': saldo_texto,
            'local': horas['local'],
            'origem': horas['origem'],
            'id_entrada': horas['id_entrada'],
            'id_saida': horas['id_saida']
        })

    return render_template('gestao.html', registros=processados)