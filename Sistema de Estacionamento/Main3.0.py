import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from fpdf import FPDF


# Função para gerar PDF
def gerar_pdf():
    texto = texto_relatorio.get("1.0", tk.END).strip()
    if not texto:
        messagebox.showwarning("Aviso", "Digite algum texto antes de gerar o PDF.")
        return

    # Escolher local para salvar
    caminho_arquivo = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Arquivos PDF", "*.pdf")],
        title="Salvar PDF"
    )
    if not caminho_arquivo:
        return  # Usuário cancelou

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Times", size=12)
        pdf.multi_cell(0, 10, texto)
        pdf.output(caminho_arquivo)
        messagebox.showinfo("Sucesso", f"PDF salvo em:\n{caminho_arquivo}")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF:\n{e}")


# Tabela  e conexão do banco de dados
conexao = sqlite3.connect("dados.db")
cursor  = conexao.cursor()

# Criar tabela com id, nome, cpf, placa, vaga, situacao e data de entrada e saida
cursor.execute("""
CREATE TABLE IF NOT EXISTS titulo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cpf TEXT,
    placa TEXT,
    vaga TEXT,
    hora_entrada TEXT,
    data_cadastro TEXT,
    situacao TEXT
)
""")
conexao.commit()

# =================================================================
# Variável global para o número máximo de vagas (pode ser alterada na aba de configurações)
MAX_VAGAS = 100  # Valor padrão, pode ser alterado em tempo de execução

def get_vagas_disponiveis():
    #Retorna lista de vagas disponíveis baseado no MAX_VAGAS atual
    cursor.execute("SELECT vaga FROM titulo WHERE situacao = 'Em aberto'")
    registros = cursor.fetchall()
    ocupadas  = {str(r[0]) for r in registros if r[0] is not None}
    
    # Gera vagas de 1 até MAX_VAGAS
    todas_vagas = [str(i) for i in range(1, MAX_VAGAS + 1)]
    disponiveis = [v for v in todas_vagas if v not in ocupadas]
    return disponiveis

# Verificar e adicionar colunas faltantes (migração do banco)
def verificar_e_atualizar_tabela():
    cursor.execute("PRAGMA table_info(titulo)")
    colunas_existentes  = {col[1] for col in cursor.fetchall()}
    colunas_necessarias = {"id", "nome", "cpf", "placa", "vaga", "hora_entrada", "data_cadastro", "situacao"}
    colunas_faltantes   = colunas_necessarias - colunas_existentes
    
    for coluna in colunas_faltantes:
        if coluna == "data_cadastro":
            cursor.execute("ALTER TABLE titulo ADD COLUMN data_cadastro TEXT")
        elif coluna == "hora_entrada":
            cursor.execute("ALTER TABLE titulo ADD COLUMN hora_entrada TEXT")
    
    if colunas_faltantes:
       conexao.commit()

verificar_e_atualizar_tabela()

# Verificar se a coluna hora_saida existe, e criar se não existir
cursor.execute("PRAGMA table_info(titulo)")
colunas_existentes = [col[1] for col in cursor.fetchall()]
if "hora_saida" not in colunas_existentes:
    cursor.execute("ALTER TABLE titulo ADD COLUMN hora_saida TEXT")
    conexao.commit()

# Função para cadastrar um novo título
def cadastrar():
    nome         = entrada_nome.get().strip()
    cpf          = entrada_cpf.get().strip()
    placa        = entrada_placa.get().strip()
    vaga         = entrada_vaga.get().strip()
    data_entrada = entrada_data.get().strip()
    hora_entrada = entrada_hora.get().strip()

    if nome and cpf and placa and vaga and data_entrada and hora_entrada:
        # Validar se a vaga está dentro do limite
        try:
            num_vaga = int(vaga)
            if num_vaga < 1 or num_vaga > MAX_VAGAS:
                messagebox.showerror("Erro", f"A vaga deve estar entre 1 e {MAX_VAGAS}.")
                return
        except ValueError:
            messagebox.showerror("Erro", "Vaga deve ser um número.")
            return
        
        # Verificar se a vaga já está ocupada
        cursor.execute("SELECT id FROM titulo WHERE vaga = ? AND situacao = 'Em aberto'", (vaga,))
        if cursor.fetchone():
            messagebox.showerror("Erro", f"Vaga {vaga} já está ocupada.")
            return
        
        cursor.execute("""
        INSERT INTO titulo (nome, cpf, placa, vaga, data_cadastro, hora_entrada, situacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nome, cpf, placa, vaga, data_entrada, hora_entrada, 'Em aberto'))
        conexao.commit()
        messagebox.showinfo("Sucesso", "Título cadastrado com sucesso!")
        
        # Limpar os campos após cadastro bem-sucedido
        entrada_nome.delete(0, tk.END)
        entrada_cpf.delete(0, tk.END)
        entrada_placa.delete(0, tk.END)
        entrada_vaga.delete(0, tk.END)
        entrada_data.delete(0, tk.END)
        entrada_hora.delete(0, tk.END)
    else:
        messagebox.showerror("Atenção", "Todos os campos devem ser preenchidos!")

# Lista para consultar vagas disponíveis para cadastro
def vagas_disponiveis_detalhado():
    #Mostra um mapa visual das vagas
    disponiveis = set(get_vagas_disponiveis())
    
    texto_vaga.delete("1.0", tk.END)
    texto_vaga.insert(tk.END, f"Mapa de Vagas (1 a {MAX_VAGAS}):\n")
    texto_vaga.insert(tk.END, "=" * 95 + "\n")
    
    # Mostrar em grid de 10 colunas
    cols = 10
    for i in range(1, MAX_VAGAS + 1, cols):
        linha = []
        for j in range(cols):
            vaga_num = i + j
            if vaga_num > MAX_VAGAS:
                break
            if str(vaga_num) in disponiveis:
                linha.append(f"{vaga_num:3} []  ")  # Disponível
            else:
                linha.append(f"{vaga_num:3} [X] ")  # Ocupada
        
        texto_vaga.insert(tk.END, " ".join(linha) + "\n")
    
    texto_vaga.insert(tk.END, "=" * 95 + "\n")
    texto_vaga.insert(tk.END, f"[] Disponível | [X] Ocupada\n")
    texto_vaga.insert(tk.END, f"Total: {len(disponiveis)} vagas disponíveis de {MAX_VAGAS}\n")

# =================================================================
# Função para os relatórios (Clientes, Recebimentos e Pendentes, Ranking de clientes)

def relatorio_totais():
    texto_relatorio.delete("1.0", tk.END)
    
    texto_relatorio.insert(tk.END, "--- Títulos Gerais ---\n\n")
    
    # Cadastros e situação geral
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN situacao = 'Em aberto' THEN 1 ELSE 0 END) as pendentes,
            SUM(CASE WHEN situacao = 'Pago' THEN 1 ELSE 0 END) as pagos
        FROM titulo
    """)
    total, pendentes, pagos = cursor.fetchone()
    total                   = total or 0
    pendentes               = pendentes or 0
    pagos                   = pagos or 0
    
    texto_relatorio.insert(tk.END, "   Cadastros \n")
    texto_relatorio.insert(tk.END, f"   Total: {total}\n")
    texto_relatorio.insert(tk.END, f"   Pendentes: {pendentes}\n")
    texto_relatorio.insert(tk.END, f"   Pagos: {pagos}\n\n")
    
    # Vagas ocupadas e disponíveis até o limite definido
    cursor.execute("SELECT COUNT(DISTINCT vaga) FROM titulo WHERE situacao = 'Em aberto'")
    vagas_ocupadas = cursor.fetchone()[0] or 0
    
    texto_relatorio.insert(tk.END, "   Vagas \n")
    texto_relatorio.insert(tk.END, f"   Total: {MAX_VAGAS}\n")
    texto_relatorio.insert(tk.END, f"   Ocupadas: {vagas_ocupadas}\n")
    texto_relatorio.insert(tk.END, f"   Disponíveis: {MAX_VAGAS - vagas_ocupadas}\n\n")

    # 3. Resumo total
    texto_relatorio.insert(tk.END, "   Análise Geral \n")
    texto_relatorio.insert(tk.END, f"   {pendentes} veículos estacionados\n")
    texto_relatorio.insert(tk.END, f"   {vagas_ocupadas} vagas ocupadas\n")
    texto_relatorio.insert(tk.END, f"   {MAX_VAGAS - vagas_ocupadas} vagas livres\n")
    texto_relatorio.insert(tk.END, f"   {pagos} pagamentos realizados\n")

def relatorio_pendentes():
    cursor.execute("SELECT * FROM titulo WHERE situacao = 'Em aberto'")
    registros = cursor.fetchall()
    texto_relatorio.delete("1.0", tk.END)
    texto_relatorio.insert(tk.END, "--- Títulos Pendentes ---\n\n")
    if not registros:
        texto_relatorio.insert(tk.END, "Nenhum título pendente.\n")
    else:
        for r in registros:
            # r = (id, nome, cpf, placa, vaga, situacao)
            texto_relatorio.insert(
                tk.END,
                f"ID {r[0]}: {r[1]} - CPF: {r[2]} - Placa: {r[3]} | Vaga: {r[4]} | Data: {r[6]}\n",
            )

def clientes_totais():
    cursor.execute("SELECT * FROM titulo")
    registros = cursor.fetchall()
    texto_relatorio.delete("1.0", tk.END)
    texto_relatorio.insert(tk.END, "--- Clientes ---\n\n")
    if not registros:
        texto_relatorio.insert(tk.END, "Nenhum cliente cadastrado.\n")
    else:
        for r in registros:
            texto_relatorio.insert(
                tk.END,
                f"ID {r[0]}: {r[1]} - CPF: {r[2]} - Placa: {r[3]} | Vaga: {r[4]} | Situação: {r[5]}\n",
            )

def ranking_clientes():
    # Modificar a consulta para limitar a 5 resultados e ordenar corretamente
    cursor.execute("""
        SELECT nome, COUNT(*) as total 
        FROM titulo 
        GROUP BY nome 
        ORDER BY total DESC            
        LIMIT 5
    """)
    registros = cursor.fetchall()
    
    texto_relatorio.delete("1.0", tk.END)
    texto_relatorio.insert(tk.END, "--- Ranking de Clientes mais frequentes ---\n\n")
    
    if not registros:
        texto_relatorio.insert(tk.END, "Nenhum cliente para ranking.\n")
    else:
        for i, r in enumerate(registros, 1):
            texto_relatorio.insert(
                tk.END, 
                f"{i}º - {r[0]} - {r[1]} {"visita" if r[1] == 1 else "visitas"}\n"
            )
        
        # Mostrar total geral
        cursor.execute("SELECT COUNT(DISTINCT nome) FROM titulo")
        total_clientes = cursor.fetchone()[0]
        texto_relatorio.insert(tk.END, f"\nTotal de clientes distintos: {total_clientes}")

# =================================================================
# Funções para máscaras de entrada
def aplicar_mascara_data(entry):
    """Aplica máscara DD/MM/YYYY no campo de data"""
    valor = entry.get().replace("/", "")
    
    if len(valor) > 8:
        valor = valor[:8]
    
    # Formatar conforme o tamanho
    if len(valor) <= 2:
        entry.delete(0, tk.END)
        entry.insert(0, valor)
    elif len(valor) <= 4:
        entry.delete(0, tk.END)
        entry.insert(0, f"{valor[:2]}/{valor[2:]}")
    else:
        entry.delete(0, tk.END)
        entry.insert(0, f"{valor[:2]}/{valor[2:4]}/{valor[4:]}")

def aplicar_mascara_hora(entry):
    """Aplica máscara HH:MM no campo de hora"""
    valor = entry.get().replace(":", "")
    
    if len(valor) > 4:
        valor = valor[:4]
    
    # Formatar conforme o tamanho
    if len(valor) <= 2:
        entry.delete(0, tk.END)
        entry.insert(0, valor)
    else:
        entry.delete(0, tk.END)
        entry.insert(0, f"{valor[:2]}:{valor[2:]}")

def aplicar_mascara_cpf(entry):
    """Aplica máscara XXX.XXX.XXX-XX no campo de CPF"""
    valor = entry.get().replace(".", "").replace("-", "")
    
    if len(valor) > 11:
        valor = valor[:11]
    
    # Formatar conforme o tamanho
    if len(valor) <= 3:
        entry.delete(0, tk.END)
        entry.insert(0, valor)
    elif len(valor) <= 6:
        entry.delete(0, tk.END)
        entry.insert(0, f"{valor[:3]}.{valor[3:]}")
    elif len(valor) <= 9:
        entry.delete(0, tk.END)
        entry.insert(0, f"{valor[:3]}.{valor[3:6]}.{valor[6:]}")
    else:
        entry.delete(0, tk.END)
        entry.insert(0, f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}")

# =================================================================
# Função para centralizar a janela na tela
def centralizar_janela(janela, largura, altura):
    # Obter dimensões da tela
    largura_tela = janela.winfo_screenwidth()
    altura_tela  = janela.winfo_screenheight()
    
    # Calcular posição central
    x = (largura_tela - largura) // 2
    y = (altura_tela - altura) // 2
    
    # Definir geometria da janela centralizada
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
# ----------------------------
# Construção da janela e abas
janela = tk.Tk()
janela.title("Controle de estacionamento")

# Definir tamanho mínimo e inicial da janela
largura_janela = 800
altura_janela  = 600
janela.minsize(largura_janela, altura_janela)

# Centralizar a janela
centralizar_janela(janela, largura_janela, altura_janela)

# Container principal para responsividade
container = tk.Frame(janela)
container.pack(expand=True, fill="both", padx=10, pady=10)

abas = ttk.Notebook(container)
abas.pack(expand=True, fill="both")

# =================================================================
# Aba de Cadastro
aba_cadastro = tk.Frame(abas)
abas.add(aba_cadastro, text="Cadastro")

# Configurar grid para responsividade
aba_cadastro.columnconfigure(1, weight=1)
aba_cadastro.rowconfigure(6, weight=1)
# ----------------------------
# Campos de entrada para cadastro
tk.Label(aba_cadastro, text="Nome do cliente:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entrada_nome = tk.Entry(aba_cadastro)
entrada_nome.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

tk.Label(aba_cadastro, text="CPF do cliente:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entrada_cpf = tk.Entry(aba_cadastro)
entrada_cpf.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
entrada_cpf.bind("<KeyRelease>", lambda e: aplicar_mascara_cpf(entrada_cpf))

tk.Label(aba_cadastro, text="Placa do veículo:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entrada_placa = tk.Entry(aba_cadastro)
entrada_placa.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

tk.Label(aba_cadastro, text="Vaga a ser ocupada:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entrada_vaga = tk.Entry(aba_cadastro)
entrada_vaga.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

tk.Label(aba_cadastro, text="Data de entrada (DD/MM/YYYY):").grid(row=4, column=0, padx=5, pady=5, sticky="e")
entrada_data = tk.Entry(aba_cadastro)
entrada_data.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
entrada_data.bind("<KeyRelease>", lambda e: aplicar_mascara_data(entrada_data))

tk.Label(aba_cadastro, text="Hora de entrada (HH:MM):").grid(row=5, column=0, padx=5, pady=5, sticky="e")
entrada_hora = tk.Entry(aba_cadastro)
entrada_hora.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
entrada_hora.bind("<KeyRelease>", lambda e: aplicar_mascara_hora(entrada_hora))

# ----------------------------
# Botão para listar vagas disponíveis
tk.Button(aba_cadastro, text="Listar vagas disponíveis", command=vagas_disponiveis_detalhado).grid(row=6, column=1, padx=5, pady=5)
texto_vaga = tk.Text(aba_cadastro, height=15, width=60)
# Exibe o widget de texto para vagas
texto_vaga.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
# Botão de cadastro
tk.Button(aba_cadastro, text="Cadastrar", command=cadastrar).grid(row=7, column=1, padx=5, pady=5)
# Configurar grid para responsividade na aba de cadastro
aba_cadastro.rowconfigure(8, weight=1)

# =================================================================
#Movimentação
aba_movimentacao = tk.Frame(abas)
abas.add(aba_movimentacao, text="Movimentação")

# Responsividade da aba
aba_movimentacao.columnconfigure(1, weight=1)
aba_movimentacao.rowconfigure(6, weight=1)

# Campo de busca por placa
tk.Label(aba_movimentacao, text="Placa do veículo (opcional):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entrada_placa_busca = tk.Entry(aba_movimentacao)
entrada_placa_busca.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# Text widget para exibir veículos
texto_movimentacao = tk.Text(aba_movimentacao, height=20, width=80)
texto_movimentacao.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

# Função para listar veículos
def listar_veiculos():
    placa_busca = entrada_placa_busca.get().strip().upper()
    texto_movimentacao.delete("1.0", tk.END)
    
    if placa_busca:
        cursor.execute("SELECT id, nome, cpf, placa, vaga, data_cadastro, hora_entrada, situacao "
                       "FROM titulo WHERE UPPER(placa) LIKE ?", (f"%{placa_busca}%",))
    else:
        cursor.execute("SELECT id, nome, cpf, placa, vaga, data_cadastro, hora_entrada, situacao FROM titulo")
    
    registros = cursor.fetchall()
    
    if not registros:
        texto_movimentacao.insert(tk.END, "Nenhum veículo encontrado.\n")
    else:
        for r in registros:
            texto_movimentacao.insert(
                tk.END,
                f"ID:{r[0]} - Nome:{r[1]} - CPF:{r[2]} - Placa:{r[3]} - Vaga:{r[4]} - Data:{r[5]} - Hora:{r[6]} - Situação:{r[7]}\n"
            )

# Botão para listar todos os veículos
tk.Button(aba_movimentacao, text="Listar todos os veículos", command=listar_veiculos).grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Campo para exclusão de registro defeituoso
tk.Label(aba_movimentacao, text="ID do registro para exclusão:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
entrada_excluir = tk.Entry(aba_movimentacao)
entrada_excluir.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

# ----------------------------
# Função para excluir registro defeituoso
def excluir_defeituoso():
    id_excluir = entrada_excluir.get().strip()
    if not id_excluir or not id_excluir.isdigit():
        messagebox.showerror("Erro", "Informe um ID válido para exclusão.")
        return
    
    confirmar = messagebox.askyesno("Confirmação", f"Tem certeza que deseja excluir o registro ID {id_excluir}?")
    if not confirmar:
        return

    cursor.execute("DELETE FROM titulo WHERE id = ?", (id_excluir,))
    conexao.commit()
    messagebox.showinfo("Sucesso", f"Registro ID {id_excluir} excluído com sucesso!")

    entrada_excluir.delete(0, tk.END)
    listar_veiculos()

# Botão para excluir registro defeituoso
tk.Button(aba_movimentacao, text="Excluir registro", command=excluir_defeituoso).grid(row=4, column=1, padx=5, pady=5, sticky="w")

# ----------------------------
# Função para excluir todos os registros e resetar IDs
def excluir_todos_registros():
    confirmar = messagebox.askyesno(
        "Confirmação",
        "Tem certeza que deseja **excluir todos os registros**? Esta ação não pode ser desfeita!"
    )
    if not confirmar:
        return

    confirmar2 = messagebox.askyesno(
        "Confirmação final",
        "Confirma mesmo que quer apagar tudo? Esta operação é irreversível!"
    )
    if not confirmar2:
        return

    cursor.execute("DELETE FROM titulo")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='titulo'")  # Resetar IDs
    conexao.commit()
    messagebox.showinfo("Sucesso", "Todos os registros foram excluídos e os IDs foram resetados!")

    listar_veiculos()

# Botão para exclusão total
tk.Button(
    aba_movimentacao,
    text    ="Excluir todos os registros",
    fg      ="red",
    command =excluir_todos_registros
).grid(row=5, column=1, padx=5, pady=5, sticky="w")

# Atualiza lista automaticamente ao abrir a aba
listar_veiculos()
  
# =================================================================
#Pagamentos
aba_pagamentos = tk.Frame(abas)
abas.add(aba_pagamentos, text="Pagamentos")

aba_pagamentos.columnconfigure(1, weight=1)
aba_pagamentos.rowconfigure(7, weight=1)

# ----------------------------
# Campo para placa ou ID
tk.Label(aba_pagamentos, text="Placa ou ID do veículo:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entrada_pagamento = tk.Entry(aba_pagamentos)
entrada_pagamento.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

# ----------------------------
# Hora de entrada (preenchida automaticamente)
tk.Label(aba_pagamentos, text="Hora de entrada:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
entrada_hora_entrada = tk.Entry(aba_pagamentos)
entrada_hora_entrada.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
entrada_hora_entrada.config(state="readonly")

# ----------------------------
# Hora de saída (usuário deve preencher)
tk.Label(aba_pagamentos, text="Hora de saída (HH:MM):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
entrada_hora_saida = tk.Entry(aba_pagamentos)
entrada_hora_saida.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
entrada_hora_saida.bind("<KeyRelease>", lambda e: aplicar_mascara_hora(entrada_hora_saida))

# ----------------------------
# Text widget para mostrar veículos em aberto
texto_pagamentos = tk.Text(aba_pagamentos, height=12, width=60)
texto_pagamentos.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

# ----------------------------
# Função para preencher hora de entrada automaticamente
def buscar_placa(event=None):
    valor = entrada_pagamento.get().strip()
    entrada_hora_entrada.config(state="normal")
    entrada_hora_entrada.delete(0, tk.END)
    if not valor:
        entrada_hora_entrada.config(state="readonly")
        return

    if valor.isdigit():
        cursor.execute("SELECT hora_entrada FROM titulo WHERE id = ?", (valor,))
    else:
        cursor.execute("SELECT hora_entrada FROM titulo WHERE UPPER(placa) = ?", (valor.upper(),))
    
    registro = cursor.fetchone()
    if registro:
        entrada_hora_entrada.insert(0, registro[0])
    entrada_hora_entrada.config(state="readonly")

entrada_pagamento.bind("<KeyRelease>", buscar_placa)

# ----------------------------
# Função para listar veículos em aberto
from math import ceil
from datetime import datetime

def listar_veiculos_pagamento():
    cursor.execute("SELECT id, nome, cpf, placa, vaga, data_cadastro, hora_entrada FROM titulo WHERE situacao='Em aberto'")
    registros = cursor.fetchall()
    texto_pagamentos.delete("1.0", tk.END)
    if not registros:
        texto_pagamentos.insert(tk.END, "Nenhum veículo com título em aberto.\n")
    else:
        for r in registros:
            texto_pagamentos.insert(
                tk.END,
                f"ID:{r[0]} - Nome:{r[1]} - CPF:{r[2]} - Placa:{r[3]} - Vaga:{r[4]} - Data:{r[5]} - Hora Entrada:{r[6]}\n"
            )

# ----------------------------
# Função para registrar pagamento
def registrar_pagamento():
    valor          = entrada_pagamento.get().strip()
    hora_saida_str = entrada_hora_saida.get().strip()

    if not valor:
        messagebox.showerror("Erro", "Informe a ID ou placa do veículo.")
        return

    if not hora_saida_str:
        messagebox.showerror("Erro", "Informe a hora de saída antes de registrar o pagamento.")
        return

    try:
        hora_saida = datetime.strptime(hora_saida_str, "%H:%M")
    except ValueError:
        messagebox.showerror("Erro", "Hora de saída inválida. Use o formato HH:MM.")
        return

    if valor.isdigit():
        cursor.execute("SELECT id, nome, placa, hora_entrada, situacao FROM titulo WHERE id = ?", (valor,))
    else:
        cursor.execute("SELECT id, nome, placa, hora_entrada, situacao FROM titulo WHERE UPPER(placa) = ?", (valor.upper(),))
    registro = cursor.fetchone()

    if not registro:
        messagebox.showerror("Erro", "Registro não encontrado.")
        return

    id_titulo, nome, placa, hora_entrada_str, situacao_atual = registro

    if situacao_atual == "Pago":
        messagebox.showinfo("Info", "Este título já está pago.")
        return

    try:
        hora_entrada = datetime.strptime(hora_entrada_str, "%H:%M")
    except ValueError:
        messagebox.showerror("Erro", f"Hora de entrada inválida no cadastro: {hora_entrada_str}")
        return

    diferenca = hora_saida - hora_entrada
    horas     = diferenca.total_seconds() / 3600
    if horas <= 0:
        messagebox.showerror("Erro", "Hora de saída deve ser posterior à hora de entrada.")
        return

    horas_cobradas = ceil(horas)
    valor_total    = horas_cobradas * 5

    cursor.execute("UPDATE titulo SET situacao='Pago', hora_saida=? WHERE id=?", (hora_saida_str, id_titulo))
    conexao.commit()

    messagebox.showinfo(
        "Pagamento Registrado",
        f"Cliente: {nome}\nPlaca: {placa}\nHora entrada: {hora_entrada_str}\nHora saída: {hora_saida_str}\nHoras cobradas: {horas_cobradas}\nValor a pagar: R${valor_total:.2f}"
    )

    entrada_pagamento.delete(0, tk.END)
    entrada_hora_saida.delete(0, tk.END)
    entrada_hora_entrada.config(state="normal")
    entrada_hora_entrada.delete(0, tk.END)
    entrada_hora_entrada.config(state="readonly")

    listar_veiculos_pagamento()

# ----------------------------
# Botão para registrar pagamento
tk.Button(aba_pagamentos, text="Registrar Pagamento", command=registrar_pagamento).grid(row=3, column=1, padx=5, pady=5)

# ----------------------------
# Consulta de pagamentos já realizados
tk.Label(aba_pagamentos, text="Consultar pagamento por ID:").grid(row=5, column=0, padx=5, pady=5, sticky="e")
entrada_consulta = tk.Entry(aba_pagamentos)
entrada_consulta.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

texto_consulta = tk.Text(aba_pagamentos, height=8, width=60)
texto_consulta.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
 
def consultar_pagamento():
    id_consulta = entrada_consulta.get().strip()
    if not id_consulta or not id_consulta.isdigit():
        messagebox.showerror("Erro", "Informe um ID válido para consulta.")
        return

    cursor.execute("SELECT nome, placa, hora_entrada, hora_saida, situacao FROM titulo WHERE id=?", (id_consulta,))
    registro = cursor.fetchone()
    
    texto_consulta.delete("1.0", tk.END)
    
    if not registro:
        texto_consulta.insert(tk.END, "Registro não encontrado.\n")
        return

    nome, placa, hora_entrada_str, hora_saida_str, situacao = registro

    if situacao != "Pago" or not hora_saida_str:
        texto_consulta.insert(tk.END, "Pagamento ainda não registrado.\n")
        return

    try:
        hora_entrada = datetime.strptime(hora_entrada_str, "%H:%M")
        hora_saida   = datetime.strptime(hora_saida_str, "%H:%M")
    except ValueError:
        texto_consulta.insert(tk.END, "Erro nos horários cadastrados.\n")
        return

    diferenca      = hora_saida - hora_entrada
    horas          = diferenca.total_seconds() / 3600
    horas_cobradas = ceil(horas)
    valor_total    = horas_cobradas * 5

    texto_consulta.insert(
        tk.END,
        f"Cliente: {nome}\nPlaca: {placa}\nHora Entrada: {hora_entrada_str}\nHora Saída: {hora_saida_str}\n"
        f"Horas cobradas: {horas_cobradas}\nValor pago: R${valor_total:.2f}\n"
    )

# Botão para consultar pagamento
tk.Button(aba_pagamentos, text="Consultar pagamento", command=consultar_pagamento).grid(row=5, column=2, padx=5, pady=5)

# ----------------------------
# Atualiza lista ao abrir a aba
listar_veiculos_pagamento()

# =================================================================
# Aba de Configurações no número de vagas
aba_config = tk.Frame(abas)
abas.add(aba_config, text="Configurações")
aba_config.columnconfigure(1, weight=1)

tk.Label(aba_config, text="Número máximo de vagas:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
entrada_max_vagas = tk.Entry(aba_config)
entrada_max_vagas.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
entrada_max_vagas.insert(0, str(MAX_VAGAS))
 
 # ----------------------------
#Função para atualizar o número máximo de vagas, com validação para não reduzir abaixo do número de vagas ocupadas
def atualizar_max_vagas():
    global MAX_VAGAS
    try:
        novo_max = int(entrada_max_vagas.get().strip())
        if novo_max < 1:
            messagebox.showerror("Erro", "O número de vagas deve ser maior que zero.")
            return
        
        # Verificar se há vagas ocupadas além do novo limite
        cursor.execute("SELECT vaga FROM titulo WHERE situacao = 'Em aberto'")
        ocupadas    = [int(r[0]) for r in cursor.fetchall() if r[0] and r[0].isdigit()]
        vagas_acima = [v for v in ocupadas if v > novo_max]
        
        if vagas_acima:
            messagebox.showerror(
                "Erro", 
                f"Não é possível reduzir para {novo_max} vagas. Existem {len(vagas_acima)} veículos em vagas acima deste número."
            )
            entrada_max_vagas.delete(0, tk.END)
            entrada_max_vagas.insert(0, str(MAX_VAGAS))
            return
        
        MAX_VAGAS = novo_max
        messagebox.showinfo("Sucesso", f"Número máximo de vagas atualizado para {MAX_VAGAS}!")
        
    except ValueError:
        messagebox.showerror("Erro", "Digite um número válido.")
# ----------------------------
tk.Button(aba_config, text="Atualizar limite de vagas", command=atualizar_max_vagas).grid(row=1, column=1, padx=5, pady=5)

#=============================================================
# Relatórios
aba_relatorios = tk.Frame(abas)
abas.add(aba_relatorios, text="Relatórios")

# Usar pack com expand para responsividade
botoes_frame = tk.Frame(aba_relatorios)
botoes_frame.pack(fill="x", padx=5, pady=5)

tk.Button(botoes_frame, text="Relatórios Gerais", command=relatorio_totais).pack(side="left", padx=5)
tk.Button(botoes_frame, text="Clientes Totais", command=clientes_totais).pack(side="left", padx=5)
tk.Button(botoes_frame, text="Mostrar Pendentes", command=relatorio_pendentes).pack(side="left", padx=5)
tk.Button(botoes_frame, text="Ranking de Clientes", command=ranking_clientes).pack(side="left", padx=5)

texto_relatorio = tk.Text(aba_relatorios, height=20, width=60)
texto_relatorio.pack(expand=True, fill="both", padx=5, pady=5)

tk.Button(botoes_frame, text="Gerar PDF", command=gerar_pdf).pack(side="right", pady=5)

# =================================================================
janela.mainloop()
conexao.close()