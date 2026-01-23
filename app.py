from flask import Flask, render_template, request, redirect, url_for, flash
app = Flask(__name__)
app.secret_key = 'clinica_thamiris'
registros = []

@app.route('/')
def index(): return render_template('index.html')

@app.route('/bater', methods=['POST'])
def bater():
    tipo = request.form.get('tipo')
    registros.append({'id': len(registros)+1, 'tipo': tipo, 'nome': 'Esther Julia'})
    flash(f"Bom {'trabalho' if tipo=='Entrada' else 'descanso'} meu bem 🌸")
    return redirect(url_for('index'))

@app.route('/gestao')
def gestao(): return render_template('gestao.html', registros=registros)

@app.route('/excluir/<int:id>')
def excluir(id):
    global registros
    registros = [r for r in registros if r['id'] != id]
    return redirect(url_for('gestao'))