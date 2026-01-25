from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

# ... (sua configuração de conexão com o banco aqui)

def calcular_resumo_mes(registros):
    dias_trabalhados = len(set(r['data'] for r in registros))
    total_segundos = 0
    # Agrupar por data para calcular horas (Entrada/Saída)
    pontos_por_dia = {}
    for r in registros:
        if r['data'] not in pontos_por_dia: pontos_por_dia[r['data']] = []
        pontos_por_dia[r['data']].append(r)

    for data, pontos in pontos_por_dia.items():
        # Lógica simples: ordena por hora e subtrai pares (Saída - Entrada)
        pontos.sort(key=lambda x: x['hora'])
        for i in range(0, len(pontos) - 1, 2):
            if pontos[i]['tipo'] == 'Entrada' and pontos[i+1]['tipo'] == 'Saída':
                fmt = '%H:%M'
                e = datetime.strptime(pontos[i]['hora'], fmt)
                s = datetime.strptime(pontos[i+1]['hora'], fmt)
                total_segundos += (s - e).total_seconds()

    horas_totais = total_segundos / 3600
    # Meta: 6h por dia trabalhado
    meta_horas = dias_trabalhados * 6
    horas_extras = horas_totais - meta_horas
    
    return dias_trabalhados, f"{horas_totais:.1f}", f"{horas_extras:.1f}"

@app.route('/gestao')
def gestao():
    mes = request.args.get('mes', datetime.now().strftime('%m'))
    # Busque os registros do banco filtrando pelo mês...
    registros = buscar_registros_banco(mes) # Sua função de busca
    
    dias, total_h, extras = calcular_resumo_mes(registros)
    
    return render_template('gestao.html', 
                           registros=registros, 
                           mes_atual=mes,
                           dias=dias, 
                           total_h=total_h, 
                           extras=extras)

@app.route('/excluir/<int:id>')
def excluir(id):
    # Lógica para deletar do Postgres: DELETE FROM pontos WHERE id = %s
    deletar_registro(id)
    return redirect(url_for('gestao'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    data = request.form.get('data') # formato YYYY-MM-DD
    hora = request.form.get('hora')
    tipo = request.form.get('tipo')
    # Salvar no banco com geo='Manual'
    salvar_no_banco(data, hora, tipo, "Manual")
    return redirect(url_for('gestao'))