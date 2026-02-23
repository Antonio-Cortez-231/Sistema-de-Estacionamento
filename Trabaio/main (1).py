import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# Tabela  e conexão do banco de dados
conexao = sqlite3.connect("dados.db")
cursor  = conexao.cursor()

# Lista de vagas disponíveis (1 a 20)
total_vagas = [str(i) for i in range(1, 21)]  

cursor.execute("""
CREATE TABLE IF NOT EXISTS titulo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cpf TEXT,
    placa TEXT,
    vaga TEXT,
    situacao TEXT DEFAULT 'Em aberto'
)
""")
conexao.commit()

# Funções para o CRUD
def cadastrar():
    nome  = entrada_nome.get().strip()
    cpf   = entrada_cpf.get().strip()
    placa = entrada_placa.get().strip()
    vaga  = entrada_vaga.get().strip()

    if nome and cpf and placa and vaga:
        cursor.execute("""
        INSERT INTO titulo (nome, cpf, placa, vaga)
        VALUES (?, ?, ?, ?)
        """, (nome, cpf, placa, vaga))
        conexao.commit()
        messagebox.showinfo("Sucesso", "Título cadastrado com sucesso!")
        
        # Limpar os campos após cadastro bem-sucedido
        entrada_nome.delete(0, tk.END)
        entrada_cpf.delete(0, tk.END)
        entrada_placa.delete(0, tk.END)
        entrada_vaga.delete(0, tk.END)
    else:
        messagebox.showerror("Atenção", "Todos os campos devem ser preenchidos!")

def listar():
    cursor.execute("SELECT * FROM titulo")
    registros = cursor.fetchall()
    # Limpa o texto antes de listar
    texto_lista.delete("1.0", tk.END)
    for r in registros:
        texto_lista.insert(tk.END, f"{r}\n")  

# Lista para consultar vagas disponíveis para cadastro
def vagas_disponiveis():
    # Recupera vagas atualmente ocupadas (situação 'Em aberto')
    cursor.execute("SELECT vaga FROM titulo WHERE situacao = 'Em aberto'")
    registros = cursor.fetchall()
    ocupadas = {str(r[0]) for r in registros if r[0] is not None}
    disponiveis = [v for v in total_vagas if v not in ocupadas]

    texto_vaga.delete("1.0", tk.END)
    if disponiveis:
        texto_vaga.insert(tk.END, "Vagas disponíveis:\n")
        for v in disponiveis:
            texto_vaga.insert(tk.END, f"{v}\n")
    else:
        texto_vaga.insert(tk.END, "Nenhuma vaga disponível.\n")

def atualizar():
    id_titulo = entrada_id.get().strip()
    nova_situacao = entrada_situacao_update.get().strip()

    if id_titulo == "" or not id_titulo.isdigit():
        messagebox.showerror("Erro", "Informe um ID válido.")
        return
    if nova_situacao not in ["Em aberto", "Pago"]:

        messagebox.showerror("Erro", "Status deve ser 'Em aberto' ou 'Pago'.")
        return

    cursor.execute("UPDATE titulo SET situacao = ? WHERE id = ?", (nova_situacao, id_titulo))
    conexao.commit()
    messagebox.showinfo("Sucesso", "Status atualizado com sucesso!")  

def excluir():
    id_titulo = entrada_id.get().strip()

    if id_titulo == "" or not id_titulo.isdigit():
        messagebox.showerror("Erro", "O id informado não é válido.")
        return

    cursor.execute("DELETE FROM titulo WHERE id = ?", (id_titulo,))
    conexao.commit()
    messagebox.showinfo("Sucesso", "Título excluído com sucesso!")

# =================================================================
# Construção da janela e abas
janela = tk.Tk()
janela.title("Controle de estacionamento")

abas = ttk.Notebook(janela)
abas.pack(expand=True, fill="both")

# =================================================================
# Cadastro
aba_cadastro = tk.Frame(abas)
abas.add(aba_cadastro, text="Cadastro")

tk.Label(aba_cadastro, text="Nome do cliente:").grid(row=0, column=0)
entrada_nome = tk.Entry(aba_cadastro)
entrada_nome.grid(row=0, column=1)

tk.Label(aba_cadastro, text="CPF do cliente:").grid(row=1, column=0)
entrada_cpf = tk.Entry(aba_cadastro)
entrada_cpf.grid(row=1, column=1)

tk.Label(aba_cadastro, text="Placa do veículo:").grid(row=2, column=0)
entrada_placa = tk.Entry(aba_cadastro)
entrada_placa.grid(row=2, column=1)

tk.Label(aba_cadastro, text="Vaga a ser ocupada:").grid(row=3, column=0)
entrada_vaga = tk.Entry(aba_cadastro)
entrada_vaga.grid(row=3, column=1)

# Botão para listar vagas disponíveis
tk.Button(aba_cadastro, text="Listar vagas disponíveis", command=vagas_disponiveis).grid(row=4, column=1)
texto_vaga = tk.Text(aba_cadastro, height=15, width=60)
# Exibe o widget de texto para vagas
texto_vaga.grid(row=6, column=0, columnspan=2, pady=5)
# Botão de cadastro
tk.Button(aba_cadastro, text="Cadastrar", command=cadastrar).grid(row=5, column=1)

# =================================================================
# Movimentação
aba_movimentacao = tk.Frame(abas)
abas.add(aba_movimentacao, text="Movimentação")

tk.Label(aba_movimentacao, text="Data:").grid(row=0, column=0)
entrada_data = tk.Entry(aba_movimentacao)
entrada_data.grid(row=0, column=1)

tk.Label(aba_movimentacao, text="Hora-Entrada:").grid(row=1, column=0)
entrada_hora = tk.Entry(aba_movimentacao)
entrada_hora.grid(row=1, column=1)

tk.Label(aba_movimentacao, text="Hora-Saída:").grid(row=2, column=0)
entrada_hora_saida = tk.Entry(aba_movimentacao)
entrada_hora_saida.grid(row=2, column=1)

tk.Label(aba_movimentacao, text="Placa do Veículo:").grid(row=3, column=0)
entrada_placa_movimento = tk.Entry(aba_movimentacao)
entrada_placa_movimento.grid(row=3, column=1)

tk.Label(aba_movimentacao, text="Valor:").grid(row=4, column=0)
entrada_valor = tk.Entry(aba_movimentacao)
entrada_valor.grid(row=4, column=1)
 
# Botão para listar registros de movimentação

tk.Button(aba_movimentacao, text="Listar movimentações", command=listar).grid(row=5, column=1)
texto_lista = tk.Text(aba_movimentacao, height=15, width=60)
texto_lista.grid(row=6, column=0, columnspan=2, pady=5)

# Botão para atualizar a movimentação em caso de novas entradas ou saídas
tk.Label(aba_movimentacao, text="ID do título para atualizar:").grid(row=7, column=0)
entrada_id = tk.Entry(aba_movimentacao)
entrada_id.grid(row=7, column=1)

# Campo para novo status e botão de atualização
tk.Label(aba_movimentacao, text="Novo status:").grid(row=8, column=0)
entrada_situacao_update = tk.Entry(aba_movimentacao)
entrada_situacao_update.grid(row=8, column=1)

tk.Button(aba_movimentacao, text="Atualizar Status", command=atualizar).grid(row=9, column=1)

#Botão para resetar disponíveis na aba de cadastro, caso queira excluir um título e liberar a vaga
tk.Button(aba_movimentacao, text="Excluir título", command=excluir).grid(row=10, column=1)

# =================================================================
# Cálculo de pagamentos
aba_pagamentos = tk.Frame(abas)
abas.add(aba_pagamentos, text="Cálculo de pagamentos")

#Campo para inserção de hora de entrada e saída, para calcular o valor a ser pago
tk.Label(aba_pagamentos, text="Hora de entrada (HH:MM):").grid(row=0, column=0)
entrada_hora_pagamento = tk.Entry(aba_pagamentos)
entrada_hora_pagamento.grid(row=0, column=1)
tk.Label(aba_pagamentos, text="Hora de saída (HH:MM):").grid(row=1, column=0)
entrada_hora_saida_pagamento = tk.Entry(aba_pagamentos)
entrada_hora_saida_pagamento.grid(row=1, column=1)

# Função para calcular o valor a ser pago com base na hora de entrada e saída de 5 reais por hora
def calcular_pagamento():
    hora_entrada = entrada_hora_pagamento.get().strip()
    hora_saida = entrada_hora_saida_pagamento.get().strip()

    try:
        h_entrada, m_entrada = map(int, hora_entrada.split(":"))
        h_saida, m_saida = map(int, hora_saida.split(":"))

        total_entrada = h_entrada * 60 + m_entrada
        total_saida = h_saida * 60 + m_saida

        if total_saida < total_entrada:
            messagebox.showerror("Erro", "Hora de saída deve ser maior que a hora de entrada.")
            return

        duracao_minutos = total_saida - total_entrada
        duracao_horas = duracao_minutos / 60
        valor_total = duracao_horas * 5  # R$5 por hora

        messagebox.showinfo("Valor a pagar", f"Valor total: R${valor_total:.2f}")
    except ValueError:
        messagebox.showerror("Erro", "Formato de hora inválido. Use HH:MM.")
        
# Botão para calcular o pagamento
tk.Button(aba_pagamentos, text="Calcular pagamento", command=calcular_pagamento).grid(row=2, column=1)

# =================================================================
# Relatórios
aba_relatorios = tk.Frame(abas)
abas.add(aba_relatorios, text="Relatórios")


# =================================================================
janela.mainloop()
conexao.close()
