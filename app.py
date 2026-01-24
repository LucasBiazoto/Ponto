@app.route('/add_manual', methods=['POST'])
def add_manual():
    if not session.get('admin_logado'): 
        return redirect(url_for('login'))
        
    data_input = request.form.get('data') # Vem do calendário (YYYY-MM-DD)
    hora_input = request.form.get('hora')
    tipo_input = request.form.get('tipo')
    
    if data_input and hora_input:
        # Converte a data para o formato 24/01/2026
        data_br = datetime.strptime(data_input, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        historico_bruto.append({
            'id': len(historico_bruto) + 1,
            'colaboradora': "Esther Julia",
            'tipo': tipo_input,
            'data': data_br,
            'hora': hora_input,
            'local': "Inserção Manual"
        })
        flash("Registro manual inserido com sucesso! 🌸")
        
    return redirect(url_for('gestao'))