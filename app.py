import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
# ... (mantenha seus imports de datetime e pytz)

# Adicione esta nova rota ao final do arquivo para o Backup
@app.route('/backup')
def backup():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data = json.dumps(registros_ponto, indent=4)
    return Response(
        data,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=backup_ponto.json"}
    )

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    resumo = {}
    total_minutos_periodo = 0
    dias_trabalhados = set() # Usamos 'set' para não contar o mesmo dia duas vezes

    for r in registros_ponto:
        if r['data'].split('/')[1] == mes_sel:
            dias_trabalhados.add(r['data']) # Registra que houve trabalho nesse dia
            chave = (r['data'], r['nome'])
            # ... (mantenha sua lógica de resumo e cálculo de saldo aqui) ...

    # No final do cálculo do gestao, conte os dias:
    qtd_dias = len(dias_trabalhados)
    
    # Adicione 'qtd_dias' no retorno do render_template
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, mes_sel=mes_sel, qtd_dias=qtd_dias)