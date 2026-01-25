import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
import pytz
import io
import json

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'
fuso = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    return psycopg2.connect(os.environ.get('POSTGRES_URL'))

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    mes_f = request.args.get('mes', datetime.now(fuso).strftime('%m'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    # Puxamos os pontos ordenados para garantir que o cálculo siga a cronologia
    cur.execute('SELECT tipo, data, hora, id FROM pontos WHERE mes = %s ORDER BY data ASC, hora ASC', (mes_f,))
    registros_raw = cur.fetchall()
    cur.close()
    conn.close()

    diario = {}
    for tipo, data, hora, p_id in registros_raw:
        if data not in diario: diario[data] = {'e': '--:--', 's': '--:--', 'id_e': None, 'id_s': None}
        if tipo == 'Entrada': 
            diario[data]['e'] = hora
            diario[data]['id_e'] = p_id
        else: 
            diario[data]['s'] = hora
            diario[data]['id_s'] = p_id

    total_minutos_mes = 0
    dias_completos = 0
    tabela_final = []

    # Lógica de Cálculo de Horas
    for data in sorted(diario.keys()):
        v = diario[data]
        cor = "#5a4a4d" # Cor padrão (escuro)
        saldo_dia_str = "00:00"
        
        if v['e'] != '--:--' and v['s'] != '--:--':
            dias_completos += 1
            # Converter horas para minutos
            h1, m1 = map(int, v['e'].split(':'))
            h2, m2 = map(int, v['s'].split(':'))
            minutos_trabalhados = (h2 * 60 + m2) - (h1 * 60 + m1)
            
            # Cálculo do Saldo (Base: 6 horas = 360 minutos)
            saldo_minutos = minutos_trabalhados - 360
            total_minutos_mes += saldo_minutos
            
            # Definir Cor com base no Saldo
            if saldo_minutos == 0: cor = "#27ae60" # Verde (Exato)
            elif saldo_minutos > 0: cor = "#2980b9" # Azul (Extra)
            else: cor = "#e74c3c" # Vermelho (Falta)
            
            sinal = "+" if saldo_minutos >= 0 else "-"
            horas_abs = abs(saldo_minutos) // 60
            mins_abs = abs(saldo_minutos) % 60
            saldo_dia_str = f"{sinal}{horas_abs:02d}:{mins_abs:02d}"
        
        tabela_final.append({
            'data': data, 'e': v['e'], 's': v['s'], 
            'id_e': v['id_e'], 'id_s': v['id_s'], 
            'cor': cor, 'saldo': saldo_dia_str
        })

    # Formatação do Saldo Total do Mês
    sinal_total = "+" if total_minutos_mes >= 0 else "-"
    total_h = abs(total_minutos_mes) // 60
    total_m = abs(total_minutos_mes) % 60
    total_mes_str = f"{sinal_total}{total_h:02d}:{total_m:02d}"

    # Invertemos a tabela para mostrar o dia mais recente no topo do painel
    return render_template('gestao.html', 
                           registros=tabela_final[::-1], 
                           total=total_mes_str, 
                           contador=dias_completos, 
                           mes_atual=mes_f)
# ... (restante das rotas bater_ponto, login e excluir permanecem iguais)