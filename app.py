import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import pytz # Necessário instalar: pip install pytz
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_premium'
SP_TZ = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    try:
        url = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url, sslmode='require')
    except: return None

@app.route('/')
def index():
    # Retorna a página inicial com geolocalização ativada no navegador
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    tipo = request.form.get('tipo')
    agora = datetime.now(SP_TZ)
    
    # Lógica de salvar com geolocalização...
    flash(f"{'Bom trabalho' if tipo=='entrada' else 'Bom descanso'} meu bem!", "success")
    return redirect(url_for('index'))

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        if request.form.get('senha') == '8340':
            return redirect(url_for('painel_gestao', auth='true'))
        flash("Senha incorreta!", "danger")
    return render_template('login_admin.html')

@app.route('/painel_gestao')
def painel_gestao():
    if request.args.get('auth') != 'true':
        return redirect(url_for('login_admin'))
    
    # Lógica para buscar pontos, calcular horas extras (Base 6h) e aplicar filtros...
    return render_template('painel_gestao.html')

@app.route('/excluir/<int:id>')
def excluir_ponto(id):
    # Lógica de exclusão...
    return redirect(url_for('painel_gestao', auth='true'))