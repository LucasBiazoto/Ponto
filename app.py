import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026_premium'

# --- CONEXÃO COM O BANCO DE DADOS ---
def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url, sslmode='require')
    except Exception as e:
        print(f"Erro na conexão com o banco: {e}")
        return None

# --- INICIALIZAÇÃO DO BANCO ---
def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Tabela de Funcionários
            cur.execute('CREATE TABLE IF NOT EXISTS funcionarios (id SERIAL PRIMARY KEY, nome TEXT NOT NULL UNIQUE);')
            # Tabela de Pontos
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pontos (
                    id SERIAL PRIMARY KEY,
                    funcionario_id INTEGER REFERENCES funcionarios(id),
                    entrada TIMESTAMP WITHOUT TIME ZONE,
                    saida TIMESTAMP WITHOUT TIME ZONE
                );
            ''')
            # Garante que a Esther Julia exista
            cur.execute("INSERT INTO funcionarios (nome) VALUES ('Esther Julia') ON CONFLICT (nome) DO NOTHING")
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")

# --- ROTA PRINCIPAL ---
@app.route('/')
def index():
    init_db()
    # Fallback caso o banco esteja offline (para o site não ficar branco)
    funcionarios = [{'id': 1, 'nome': 'Esther Julia'}]
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT * FROM funcionarios ORDER BY nome')
            db_funcs = cur.fetchall()
            if db_funcs:
                funcionarios = db_funcs
            cur.close()
            conn.close()
        except:
            pass
            
    return render_template('index.html', funcionarios=funcionarios)

# --- ROTA PARA BATER PONTO ---
@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    funcionario_id = request.form.get('funcionario_id')
    tipo = request.form.get('tipo')
    agora = datetime.now()
    
    # Suas frases personalizadas 🌸
    mensagem = 'Bom trabalho meu bem' if tipo == 'entrada' else 'Bom descanso meu bem'
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            if tipo == 'entrada':
                cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (funcionario_id, agora))
            else:
                # Fecha o último ponto aberto daquele funcionário
                cur.execute('''
                    UPDATE pontos SET saida = %s 
                    WHERE funcionario_id = %s AND saida IS NULL
                ''', (agora, funcionario_id))
            conn.commit()
            cur.close()
            conn.close()
            flash(mensagem, 'success')
        except Exception as e:
            flash('Erro ao salvar, tente novamente!', 'danger')
    else:
        # Se o banco falhar, ainda mostramos a mensagem para o visual ficar ok
        flash(f"{mensagem} (Modo Offline)", 'success')
        
    return redirect(url_for('index'))

# --- ROTA DE GESTÃO (PAINEL RESTRITO) ---
@app.route('/painel_gestao')
def painel_gestao():
    # Validação de senha via URL
    senha = request.args.get('senha')
    if senha != "8340":
        flash("Senha incorreta ou acesso negado.", "danger")
        return redirect(url_for('index'))
        
    pontos = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # Busca pontos com LEFT JOIN para garantir que a página abra sempre
            cur.execute('''
                SELECT f.nome, p.entrada, p.saida 
                FROM funcionarios f 
                LEFT JOIN pontos p ON f.id = p.funcionario_id 
                ORDER BY p.entrada DESC NULLS LAST
            ''')
            pontos = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erro na gestão: {e}")
            
    return render_template('painel_gestao.html', pontos=pontos)

if __name__ == '__main__':
    app.run(debug=True)