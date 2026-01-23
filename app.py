import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_2026'
SP_TZ = pytz.timezone('America/Sao_Paulo')

def get_db_connection():
    try:
        # A Vercel usará a DATABASE_URL do seu banco de dados
        url = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(url, sslmode='require')
    except: 
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    nome_colaboradora = request.form.get('colaboradora')
    tipo = request.form.get('tipo') # Recebe 'Entrada' ou 'Saída'
    agora = datetime.now(SP_TZ)
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        # Primeiro, garantimos que a funcionária existe no banco ou usamos o nome direto
        if tipo == 'Entrada':
            cur.execute('INSERT INTO pontos (funcionario_nome, entrada) VALUES (%s, %s)', (nome_colaboradora, agora))
            flash(f'Bom trabalho meu bem, {nome_colaboradora}! 🌸')
        else:
            cur.execute('UPDATE pontos SET saida = %s WHERE funcionario_nome = %s AND saida IS NULL', (agora, nome_colaboradora))
            flash(f'Bom descanso meu bem, {nome_colaboradora}! ✨')
        
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/login')
def login():
    # Esta rota leva para a área restrita
    return render_template('painel_gestao.html') # Ou sua página de login