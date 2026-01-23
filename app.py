from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')

# Lista de registros (em um projeto real usaríamos banco de dados)
registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso_horario)
    
    registros_ponto.append({
        'nome': nome, 
        'tipo': tipo, 
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M:%S')
    })

    if tipo == 'Entrada':
        flash(f"Bom trabalho meu bem! 🌸 Ponto de {tipo} batido às {agora.strftime('%H:%M:%S')}")
    else:
        flash(f"Bom descanso meu bem! 🌸 Ponto de {tipo} batido às {agora.strftime('%H:%M:%S')}")
    
    return redirect(url_for('index'))

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
    if not session.get('admin_logado'):
        return redirect(url_for('login'))
    return render_template('gestao.html', registros=registros_ponto)

@app.route('/logout')
def logout():
    session.pop('admin_logado', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)