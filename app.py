from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'
ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')

registros_ponto = [] # Onde ficam armazenadas as batidas

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    
    # Filtros de Mês e Ano
    agora = datetime.now(fuso_horario)
    mes_sel = request.args.get('mes', agora.strftime('%m'))
    ano_sel = request.args.get('ano', agora.strftime('%Y'))
    
    resumo = {}
    total_minutos_periodo = 0

    for r in registros_ponto:
        r_data = datetime.strptime(r['data'], '%d/%m/%Y')
        # Filtra pelo mês e ano escolhidos
        if r_data.strftime('%m') == mes_sel and r_data.strftime('%Y') == ano_sel:
            chave = (r['data'], r['nome'])
            if chave not in resumo:
                resumo[chave] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None, 'loc': 'N/A'}
            
            if r['tipo'] == 'Entrada':
                resumo[chave]['e'] = r['hora']
                resumo[chave]['id_e'] = r['id']
                resumo[chave]['loc'] = r.get('local', 'N/A')
            else:
                resumo[chave]['s'] = r['hora']
                resumo[chave]['id_s'] = r['id']

    dados_finais = []
    for (data, nome), v in resumo.items():
        saldo_str, cor_status = "00:00", "azul"
        if v['e'] != '--:--' and v['s'] != '--:--':
            try:
                h1, m1 = map(int, v['e'].split(':'))
                h2, m2 = map(int, v['s'].split(':'))
                diff = (h2 * 60 + m2) - (h1 * 60 + m1) - 360 # Base 6h
                total_minutos_periodo += diff
                
                if diff > 0: cor_status = "verde"
                elif diff < 0: cor_status = "vermelho"
                
                sinal = "+" if diff >= 0 else "-"
                abs_m = abs(diff)
                saldo_str = f"{sinal}{abs_m//60:02d}:{abs_m%60:02d}"
            except: pass
            
        dados_finais.append({
            'data': data, 'nome': nome, 'e': v['e'], 's': v['s'],
            'id_e': v['id_e'], 'id_s': v['id_s'], 'saldo': saldo_str, 
            'loc': v['loc'], 'cor': cor_status
        })

    # Formata o saldo total do mês
    sinal_t = "+" if total_minutos_periodo >= 0 else "-"
    abs_t = abs(total_minutos_periodo)
    soma_total = f"{sinal_t}{abs_t//60:02d}:{abs_t%60:02d}"

    return render_template('gestao.html', registros=dados_finais, soma_total=soma_total, mes_sel=mes_sel, ano_sel=ano_sel)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))