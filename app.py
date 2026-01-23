from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')
registros_ponto = [] 

def calcular_resumo():
    resumo = {}
    # Organiza entradas e saídas por (Nome, Data)
    for r in registros_ponto:
        chave = (r['nome'], r['data'])
        if chave not in resumo:
            resumo[chave] = {'entrada': None, 'saida': None}
        if r['tipo'] == 'Entrada': resumo[chave]['entrada'] = r['hora']
        elif r['tipo'] == 'Saída': resumo[chave]['saida'] = r['hora']
    
    lista_final = []
    total_dias = {}
    
    for (nome, data), horas in resumo.items():
        saldo_str = "00:00"
        if horas['entrada'] and horas['saida']:
            # Cálculo de horas e minutos
            h1 = datetime.strptime(horas['entrada'], '%H:%M')
            h2 = datetime.strptime(horas['saida'], '%H:%M')
            diff = h2 - h1
            
            segundos_trabalhados = diff.total_seconds()
            segundos_base = 6 * 3600 # 6 horas
            saldo_segundos = segundos_trabalhados - segundos_base
            
            sinal = "+" if saldo_segundos >= 0 else "-"
            abs_saldo = abs(saldo_segundos)
            horas_s = int(abs_saldo // 3600)
            minutos_s = int((abs_saldo % 3600) // 60)
            saldo_str = f"{sinal}{horas_s:02d}:{minutos_s:02d}"
            
            total_dias[nome] = total_dias.get(nome, 0) + 1
            
        lista_final.append({
            'nome': nome, 'data': data,
            'entrada': horas['entrada'] or '--:--',
            'saida': horas['saida'] or '--:--',
            'extra': saldo_str
        })
    return sorted(lista_final, key=lambda x: x['data'], reverse=True), total_dias

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso_horario)
    # Formato ajustado para apenas Hora:Minuto
    hora_limpa = agora.strftime('%H:%M')
    data_limpa = agora.strftime('%d/%m/%Y')
    
    registros_ponto.append({
        'id': len(registros_ponto), 'nome': nome, 'tipo': tipo, 
        'data': data_limpa, 'hora': hora_limpa
    })
    
    msg = "Bom trabalho meu bem! 🌸" if tipo == 'Entrada' else "Bom descanso meu bem! 🌸"
    flash(f"{msg} Ponto de {tipo} batido às {hora_limpa}")
    return redirect(url_for('index'))

@app.route('/inserir_manual', methods=['POST'])
def inserir_manual():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    data_br = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%d/%m/%Y')
    registros_ponto.append({
        'id': len(registros_ponto),
        'nome': request.form.get('nome'), 'tipo': request.form.get('tipo'),
        'data': data_br, 'hora': request.form.get('hora')
    })
    flash("Registro manual adicionado! ✨")
    return redirect(url_for('gestao'))

@app.route('/excluir/<int:index>')
def excluir(index):
    if session.get('admin_logado'):
        # Como estamos usando lista simples, removemos pelo índice
        if 0 <= index < len(registros_ponto):
            registros_ponto.pop(index)
    return redirect(url_for('gestao'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
        flash("Senha incorreta!")
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'): return redirect(url_for('login'))
    dados, totais = calcular_resumo()
    return render_template('gestao.html', registros=dados, totais=totais)

@app.route('/logout')
def logout():
    session.pop('admin_logado', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)