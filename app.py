from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'chave_secreta_thamiris'
fuso = pytz.timezone('America/Sao_Paulo')

# Lista para salvar os pontos (Em produção, ideal seria um banco de dados)
registros_ponto = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome = request.form.get('colaboradora')
    tipo = request.form.get('tipo')
    agora = datetime.now(fuso)
    
    registros_ponto.append({
        'nome': nome, 'tipo': tipo,
        'data': agora.strftime('%d/%m/%Y'),
        'hora': agora.strftime('%H:%M'),
        'local': 'Unidade Penha'
    })
    
    # MENSAGENS CARINHOSAS QUE VOCÊ PEDIU
    if tipo == 'Entrada':
        flash("Bom trabalho meu bem 🌸")
    else:
        flash("Bom descanso meu bem 🌸")
        
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/gestao')
def gestao():
    # Aqui renderizamos a tela de gestão que você aprovou
    return render_template('gestao.html', registros=registros_ponto, soma_total="+00:00")

if __name__ == '__main__':
    app.run(debug=True)