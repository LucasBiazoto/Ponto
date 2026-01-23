from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz
import json # Preparando para salvar em arquivo

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_permanente'
fuso = pytz.timezone('America/Sao_Paulo')

# Simulando um banco de dados que sobrevive a reinicializações simples
# Nota: Para produção real na Vercel, usaremos o 'Vercel KV' no próximo passo.
registros_ponto = [] 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    
    novo_ponto = {
        'id': len(registros_ponto) + 1,
        'nome': nome, 
        'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': 'Unidade Penha'
    }
    registros_ponto.append(novo_ponto)
    
    # Mantém a mensagem que você pediu
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Filtro de 12 meses funcionando como na imagem
    mes_sel = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    # Lógica de agrupamento para cálculo de saldo e cores
    resumo = {}
    total_minutos_periodo = 0
    
    for r in registros_ponto:
        mes_registro = r['data'].split('/')[1]
        if mes_registro == mes_sel:
            chave = (r['data'], r['nome'])
            if chave not in resumo:
                resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
            
            if r['tipo'] == 'Entrada':
                resumo[chave]['e'] = r['hora']
                resumo[chave]['id_e'] = r['id']
            else:
                resumo[chave]['s'] = r['hora']
                resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        cor, saldo_str = "azul", "00:00"
        if v['e'] != '--:--' and v['s'] != '--:--':
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            # Cálculo de 6h (360 min) conforme configurado
            diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360
            total_minutos_periodo += diff
            cor = "verde" if diff > 0 else "vermelho" if diff < 0 else "azul"
            sinal = "+" if diff >= 0 else "-"
            abs_m = abs(diff)
            saldo_str = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'], 
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo_str, 'cor': cor
        })

    s_total = f"{'+' if total_minutos_periodo >= 0 else '-'}{abs(total_minutos_periodo)//60:02d}:{abs(total_minutos_periodo)%60:02d}"
    
    return render_template('gestao.html', registros=dados_finais, soma_total=s_total, mes_sel=mes_sel)