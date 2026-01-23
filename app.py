from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_secret'

# Configuração da senha e fuso horário
ADMIN_PASSWORD = "8340"
fuso_horario = pytz.timezone('America/Sao_Paulo')

# Lista para armazenar os registros (em produção ideal seria um banco de dados)
registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', method=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    hora_atual = datetime.now(fuso_horario).strftime('%d/%m/%Y %H:%M:%S')

    # Salvando o registro
    registros_ponto.append({'nome': nome, 'tipo': tipo, 'horario': hora_atual})

    # Mensagens carinhosas personalizadas
    if tipo == 'Entrada':
        flash(f"Bom trabalho meu bem! 🌸 Ponto de {tipo} batido às {hora_atual}")
    else:
        flash(f"Bom descanso meu bem! 🌸 Ponto de {tipo} batido às {hora_atual}")

    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('password')
        if senha == ADMIN_PASSWORD:
            session['admin_logado'] = True
            return redirect(url_for('gestao'))
        else:
            flash("Senha incorreta, tente novamente.")
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    if not session.get('admin_logado'):
        return redirect(url_for('login'))
    return render_template('gestao.html', registros=registros_ponto)

if __name__ == '__main__':
    app.run(debug=True)