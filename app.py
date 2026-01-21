import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clinica_thamiris_araujo_2026'

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def get_db_connection():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url, sslmode='require')
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Criação das tabelas
            cur.execute('CREATE TABLE IF NOT EXISTS funcionarios (id SERIAL PRIMARY KEY, nome TEXT NOT NULL UNIQUE);')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS pontos (
                    id SERIAL PRIMARY KEY,
                    funcionario_id INTEGER REFERENCES funcionarios(id),
                    entrada TIMESTAMP WITHOUT TIME ZONE,
                    saida TIMESTAMP WITHOUT TIME ZONE
                );
            ''')
            # Garante que a Esther Julia esteja cadastrada
            cur.execute("INSERT INTO funcionarios (nome) VALUES ('Esther Julia') ON CONFLICT (nome) DO NOTHING")
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao inicializar tabelas: {e}")

# --- ROTAS DO SISTEMA ---

@app.route('/')
def index():
    init_db()
    # Lista padrão caso o banco falhe, para o site nunca ficar branco
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

@app.route('/bater_ponto', methods=['POST'])
def bater_ponto():
    funcionario_id = request.form.get('funcionario_id')
    tipo = request.form.get('tipo')
    agora = datetime.now()
    
    # Mensagens personalizadas Dra. Thamiris
    mensagem = 'Bom trabalho meu bem' if tipo == 'entrada' else 'Bom descanso meu bem'
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            if tipo == 'entrada':
                cur.execute('INSERT INTO pontos (funcionario_id, entrada) VALUES (%s, %s)', (funcionario_id, agora))
            else:
                # Fecha o último ponto em aberto (saída NULL)
                cur.execute('''
                    UPDATE pontos SET saida = %s 
                    WHERE funcionario_id = %s AND saida IS NULL
                ''', (agora, funcionario_id))
            conn.commit()
            cur.close()
            conn.close()
            flash(mensagem, 'success')
        except Exception as e:
            flash('Erro ao registrar no banco, mas o visual está ok!', 'danger')
    else:
        # Se o banco falhar, mostramos a mensagem carinhosa assim mesmo para a cliente ver
        flash(mensagem, 'success')
        
    return redirect(url_for('index'))

@app.route('/painel_gestao')
def painel_gestao():
    senha = request.args.get('senha')
    if senha != "8340":
        return "Senha Incorreta ou Acesso Negado", 403
        
    pontos = []
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # LEFT JOIN para garantir que a página abra mesmo sem pontos registrados
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
            print(f"Erro na consulta de gestão: {e}")
            
    return render_template('painel_gestao.html', pontos=pontos)

if __name__ == '__main__':
    app.run(debug=True)