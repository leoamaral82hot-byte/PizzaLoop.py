from datetime import datetime, timedelta
from tkinter import *
from tkinter import messagebox, ttk, filedialog
import csv

PIZZAS = [
    ("Pizza 1", "Calabresa", 34.90),
    ("Pizza 2", "Mussarela", 32.90),
    ("Pizza 3", "Portuguesa", 38.90),
    ("Pizza 4", "Frango com Catupiry", 39.90),
    ("Pizza 5", "Quatro Queijos", 41.90),
    ("Pizza 6", "Pepperoni", 42.90),
    ("Pizza 7", "Marguerita", 36.90),
    ("Pizza 8", "Atum", 37.90),
    ("Pizza 9", "Bacon", 40.90),
    ("Pizza 10", "Chocolate", 35.90),
]

STATUS_OPCOES = ["Novo", "Em preparo", "Saiu para entrega", "Entregue", "Cancelado"]
PAGAMENTOS = ["Pix", "Dinheiro", "Crédito", "Débito"]

# Paleta inspirada em pizzaria
COR_BG = "#fff7ed"
COR_CARD = "#fff1e6"
COR_SIDEBAR = "#922b21"
COR_SIDEBAR_TXT = "#fde8da"
COR_PRIMARIA = "#d35400"
COR_TEXTO = "#42210b"
COR_MUTED = "#8b5a2b"
COR_BORDA = "#e4c8b5"
COR_CLIENTE_COM_PEDIDO = "#1b5e20"
COR_CLIENTE_SEM_PEDIDO = COR_TEXTO

numero_pedido = 1
item_selecionado = None
preco_selecionado = None
cliente_selecionado = None
botoes_clientes = {}
frame_lista_clientes = None

pedidos_dados = []
clientes_cadastrados = []
filtro_inicio_data = None
filtro_fim_data = None
status_filtro = "Todos"
busca_filtro = ""

janela_relatorio = None
lbl_faturamento_bruto = None
lbl_faturamento_liquido = None
lbl_total_cancelado = None
lbl_qtd_pedidos = None
lbl_ticket_medio = None
ent_data_inicio = None
ent_data_fim = None
canvas_grafico = None
canvas_grafico_receita = None

janela_dashboard = None
dash_lbl_total_vendas = None
dash_lbl_qtd_pedidos = None
dash_lbl_ticket_medio = None
dash_lbl_clientes = None
dash_canvas_status = None
dash_frame_recentes = None
dash_frame_mais_vendidas = None
dash_frame_pagamentos = None


def to_date_br(texto_data):
    return datetime.strptime(texto_data, "%d/%m/%Y").date()


def selecionar_cliente(nome):
    global cliente_selecionado
    cliente_selecionado = nome
    ent_cliente.delete(0, END)
    ent_cliente.insert(0, nome)
    mensagem_status.config(text=f"Cliente '{nome}' selecionado.")
    for cliente, botao in botoes_clientes.items():
        if cliente == nome:
            botao.config(bg=COR_PRIMARIA, fg="white")
        else:
            cor_txt = COR_CLIENTE_COM_PEDIDO if cliente in {pedido["cliente"] for pedido in pedidos_dados} else COR_CLIENTE_SEM_PEDIDO
            botao.config(bg=COR_CARD, fg=cor_txt)


def atualizar_lista_clientes():
    for widget in frame_lista_clientes.winfo_children():
        widget.destroy()
    botoes_clientes.clear()

    clientes_com_pedido = {pedido["cliente"] for pedido in pedidos_dados}
    for i, nome in enumerate(sorted(clientes_cadastrados)):
        cor_txt = COR_CLIENTE_COM_PEDIDO if nome in clientes_com_pedido else COR_CLIENTE_SEM_PEDIDO
        nome_botao = f"✅ {nome}" if nome in clientes_com_pedido else nome
        botao = Button(
            frame_lista_clientes,
            text=nome_botao,
            command=lambda n=nome: selecionar_cliente(n),
            bg=COR_CARD,
            fg=cor_txt,
            bd=1,
            relief="solid",
            anchor="w",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10,
            cursor="hand2",
        )
        botao.grid(row=i, column=0, sticky="ew", padx=4, pady=4)
        botoes_clientes[nome] = botao
    frame_lista_clientes.grid_columnconfigure(0, weight=1)


def selecionar_item(nome, sabor, preco):
    item_selecionado.set(f"{nome} - {sabor}")
    preco_selecionado.set(preco)
    lbl_item.config(text=f"Item: {item_selecionado.get()}")
    lbl_total.config(text=f"Total: R$ {preco_selecionado.get():.2f}")
    mensagem_status.config(text="Item selecionado, complete cliente e pagamento.")


def cadastrar_cliente():
    nome = ent_novo_cliente.get().strip()
    if not nome:
        messagebox.showwarning("Clientes", "Digite o nome do cliente.")
        return
    if nome in clientes_cadastrados:
        messagebox.showinfo("Clientes", "Cliente já cadastrado.")
        return
    clientes_cadastrados.append(nome)
    atualizar_lista_clientes()
    ent_novo_cliente.delete(0, END)
    mensagem_status.config(text=f"Cliente '{nome}' cadastrado com sucesso.")


def remover_cliente():
    """Remove o cliente selecionado do cadastro, se não houver pedidos associados."""
    global cliente_selecionado
    nome = cliente_selecionado
    if not nome:
        messagebox.showinfo("Clientes", "Selecione um cliente na lista para remover.")
        return

    # Verifica se existem pedidos associados ao cliente
    possui_pedidos = any(p for p in pedidos_dados if p.get("cliente") == nome)
    if possui_pedidos:
        messagebox.showwarning(
            "Clientes",
            "Não é possível remover o cliente porque existem pedidos associados a ele."
        )
        return

    if nome not in clientes_cadastrados:
        messagebox.showinfo("Clientes", "Cliente não está cadastrado.")
        cliente_selecionado = None
        return

    confirmar = messagebox.askyesno("Remover cliente", f"Deseja remover o cliente '{nome}' do cadastro?")
    if not confirmar:
        return

    # Remove e atualiza a interface
    clientes_cadastrados.remove(nome)
    cliente_selecionado = None
    try:
        ent_cliente.delete(0, END)
    except Exception:
        pass
    atualizar_lista_clientes()
    mensagem_status.config(text=f"Cliente '{nome}' removido do cadastro.")


def carregar_cliente_selecionado(_event=None):
    return


def filtrar_pedidos():
    global busca_filtro
    busca_filtro = ent_busca.get().strip().lower()
    aplicar_filtro_tabela()


def alterar_filtro_status(novo_status):
    global status_filtro
    status_filtro = novo_status
    for status, botao in botoes_status.items():
        if status == novo_status:
            botao.config(bg=COR_PRIMARIA, fg="white")
        else:
            botao.config(bg="#f1f5f9", fg=COR_TEXTO)
    aplicar_filtro_tabela()


def obter_pedidos_filtrados_tabela():
    resultado = []
    for pedido in pedidos_dados:
        if status_filtro != "Todos" and pedido["status"] != status_filtro:
            continue
        alvo = f"{pedido['numero']} {pedido['cliente']} {pedido['item']}".lower()
        if busca_filtro and busca_filtro not in alvo:
            continue
        resultado.append(pedido)
    return resultado


def aplicar_filtro_tabela():
    tabela.delete(*tabela.get_children())
    pedidos_filtrados = obter_pedidos_filtrados_tabela()
    for pedido in pedidos_filtrados:
        tabela.insert(
            "",
            END,
            values=(
                f"#{pedido['numero']}",
                pedido["data_hora_str"],
                pedido["cliente"],
                pedido["item"],
                f"R$ {pedido['total']:.2f}",
                pedido["pagamento"],
                pedido["status"],
                "Atualizar | Excluir",
            ),
            tags=(pedido["status"],),
        )
    lbl_count.config(text=f"Mostrando {len(pedidos_filtrados)} pedido(s)")
    atualizar_relatorio()
    atualizar_dashboard()


def registrar_pedido():
    global numero_pedido

    cliente = ent_cliente.get().strip()
    pagamento = cmb_pagamento.get().strip()
    item = item_selecionado.get()
    total = preco_selecionado.get()

    if not cliente:
        messagebox.showwarning("Campos obrigatórios", "Informe o nome do cliente.")
        return
    if item == "Nenhum item selecionado":
        messagebox.showwarning("Campos obrigatórios", "Selecione uma pizza.")
        return
    if pagamento not in PAGAMENTOS:
        messagebox.showwarning("Campos obrigatórios", "Selecione a forma de pagamento.")
        return

    data_hora_obj = datetime.now()
    pedido = {
        "numero": numero_pedido,
        "data_hora_obj": data_hora_obj,
        "data_hora_str": data_hora_obj.strftime("%d/%m/%Y %H:%M"),
        "cliente": cliente,
        "item": item,
        "total": float(total),
        "pagamento": pagamento,
        "status": "Novo",
    }
    pedidos_dados.append(pedido)
    atualizar_lista_clientes()

    if cliente not in clientes_cadastrados:
        clientes_cadastrados.append(cliente)
        atualizar_lista_clientes()

    numero_pedido += 1
    limpar_formulario()
    aplicar_filtro_tabela()
    mensagem_status.config(text=f"Pedido #{pedido['numero']} registrado com sucesso.")


def limpar_formulario():
    ent_cliente.delete(0, END)
    cmb_pagamento.set("")
    item_selecionado.set("Nenhum item selecionado")
    preco_selecionado.set(0.0)
    lbl_item.config(text="Item: Nenhum item selecionado")
    lbl_total.config(text="Total: R$ 0.00")


def get_numero_pedido_selecionado():
    selecionado = tabela.selection()
    if not selecionado:
        messagebox.showinfo("Pedidos", "Selecione um pedido na tabela.")
        return None
    valores = tabela.item(selecionado[0], "values")
    return int(str(valores[0]).replace("#", ""))


def alterar_status(novo_status):
    numero = get_numero_pedido_selecionado()
    if numero is None:
        return
    for pedido in pedidos_dados:
        if pedido["numero"] == numero:
            pedido["status"] = novo_status
            break
    aplicar_filtro_tabela()
    mensagem_status.config(text=f"Pedido #{numero} atualizado para {novo_status}.")


def excluir_pedido():
    numero = get_numero_pedido_selecionado()
    if numero is None:
        return
    alvo = next((p for p in pedidos_dados if p["numero"] == numero), None)
    if alvo is None:
        return
    confirmar = messagebox.askyesno(
        "Excluir pedido", f"Deseja excluir o pedido #{numero} de {alvo['cliente']}?"
    )
    if not confirmar:
        return
    pedidos_dados.remove(alvo)
    atualizar_lista_clientes()
    aplicar_filtro_tabela()
    mensagem_status.config(text=f"Pedido #{numero} excluído.")


def obter_pedidos_filtrados_relatorio():
    pedidos_filtrados = []
    for pedido in pedidos_dados:
        if filtro_inicio_data and pedido["data_hora_obj"].date() < filtro_inicio_data:
            continue
        if filtro_fim_data and pedido["data_hora_obj"].date() > filtro_fim_data:
            continue
        pedidos_filtrados.append(pedido)
    return pedidos_filtrados


def desenhar_grafico_status(status_counts):
    if canvas_grafico is None:
        return
    canvas_grafico.delete("all")
    dados = [
        ("Novo", status_counts.get("Novo", 0), "#f59e0b"),
        ("Em preparo", status_counts.get("Em preparo", 0), "#f59e0b"),
        ("Saiu para entrega", status_counts.get("Saiu para entrega", 0), "#3b82f6"),
        ("Entregue", status_counts.get("Entregue", 0), "#22c55e"),
        ("Cancelado", status_counts.get("Cancelado", 0), "#ef4444"),
    ]
    total = sum(valor for _, valor, _ in dados)
    max_valor = max(1, max(valor for _, valor, _ in dados))
    x = 28
    base = 210
    largura = 70
    canvas_grafico.create_line(20, base, 500, base, fill="#cbd5e1", dash=(2, 2))

    for nome, valor, cor in dados:
        altura = int((valor / max_valor) * 160)
        y1 = base - altura
        y2 = base
        canvas_grafico.create_rectangle(x, y1, x + largura, y2, fill=cor, outline="")
        percentual = int((valor / total) * 100) if total else 0
        canvas_grafico.create_text(
            x + largura // 2,
            y1 - 14,
            text=f"{valor} ({percentual}%)",
            fill=COR_TEXTO,
            font=("Arial", 9, "bold"),
        )
        canvas_grafico.create_text(
            x + largura // 2,
            y2 + 18,
            text=nome,
            fill=COR_MUTED,
            font=("Arial", 9),
        )
        x += largura + 24


def desenhar_grafico_receita(faturamento_bruto, faturamento_liquido, valor_cancelado, pagamentos):
    if canvas_grafico_receita is None:
        return
    canvas_grafico_receita.delete("all")
    dados = [
        ("Bruto", faturamento_bruto, "#d97706"),
        ("Líquido", faturamento_liquido, "#16a34a"),
        ("Cancelado", valor_cancelado, "#ef4444"),
    ]
    max_valor = max(1.0, max(valor for _, valor, _ in dados))
    x = 30
    base = 220
    largura = 70
    canvas_grafico_receita.create_line(20, base, 380, base, fill="#cbd5e1", dash=(2, 2))

    for nome, valor, cor in dados:
        altura = int((valor / max_valor) * 160)
        y1 = base - altura
        y2 = base
        canvas_grafico_receita.create_rectangle(x, y1, x + largura, y2, fill=cor, outline="")
        label_text = f"{moeda_br(valor)}"
        canvas_grafico_receita.create_text(
            x + largura // 2,
            y1 - 16,
            text=label_text,
            fill=COR_TEXTO,
            font=("Arial", 9, "bold"),
        )
        canvas_grafico_receita.create_text(
            x + largura // 2,
            y2 + 18,
            text=nome,
            fill=COR_MUTED,
            font=("Arial", 9),
        )
        x += largura + 30

    if pagamentos:
        total = sum(pagamentos.values())
        y = 40
        canvas_grafico_receita.create_text(
            280,
            y,
            text="Receita por pagamento",
            fill=COR_TEXTO,
            font=("Arial", 9, "bold"),
        )
        for i, (meio, valor) in enumerate(pagamentos.items()):
            pct = (valor / total * 100) if total else 0
            canvas_grafico_receita.create_text(
                280,
                y + 20 + (i * 18),
                text=f"{meio}: {moeda_br(valor)} ({pct:.0f}%)",
                fill=COR_TEXTO,
                font=("Arial", 8),
            )


def atualizar_relatorio():
    pedidos = obter_pedidos_filtrados_relatorio()
    qtd = len(pedidos)
    cancelados = [p for p in pedidos if p["status"] == "Cancelado"]
    qtd_cancelados = len(cancelados)
    faturamento_bruto = sum(p["total"] for p in pedidos)
    faturamento_liquido = faturamento_bruto - sum(p["total"] for p in cancelados)
    pedidos_ativos = qtd - qtd_cancelados
    ticket = faturamento_liquido / pedidos_ativos if pedidos_ativos else 0

    status_counts = {status: 0 for status in STATUS_OPCOES}
    for p in pedidos:
        if p["status"] in status_counts:
            status_counts[p["status"]] += 1

    pagamentos = {meio: 0.0 for meio in PAGAMENTOS}
    for p in pedidos:
        pagamentos[p["pagamento"]] = pagamentos.get(p["pagamento"], 0.0) + p["total"]

    if lbl_faturamento_bruto is not None:
        lbl_faturamento_bruto.config(text=f"Faturamento bruto: {moeda_br(faturamento_bruto)}")
    if lbl_faturamento_liquido is not None:
        lbl_faturamento_liquido.config(text=f"Faturamento líquido: {moeda_br(faturamento_liquido)}")
    if lbl_total_cancelado is not None:
        lbl_total_cancelado.config(text=f"Total cancelado: {moeda_br(sum(p['total'] for p in cancelados))}")
    if lbl_qtd_pedidos is not None:
        lbl_qtd_pedidos.config(text=f"Pedidos no período: {qtd} (Cancelados: {qtd_cancelados})")
    if lbl_ticket_medio is not None:
        lbl_ticket_medio.config(text=f"Ticket médio (sem cancelados): {moeda_br(ticket)}")
    desenhar_grafico_status(status_counts)
    desenhar_grafico_receita(faturamento_bruto, faturamento_liquido, sum(p["total"] for p in cancelados), pagamentos)


def aplicar_filtro_data():
    global filtro_inicio_data, filtro_fim_data
    if ent_data_inicio is None or ent_data_fim is None:
        return
    try:
        inicio_txt = ent_data_inicio.get().strip()
        fim_txt = ent_data_fim.get().strip()
        inicio = to_date_br(inicio_txt) if inicio_txt else None
        fim = to_date_br(fim_txt) if fim_txt else None
    except ValueError:
        messagebox.showerror("Filtro", "Use formato DD/MM/AAAA.")
        return
    if inicio and fim and inicio > fim:
        messagebox.showerror("Filtro", "Data inicial maior que final.")
        return
    filtro_inicio_data = inicio
    filtro_fim_data = fim
    atualizar_relatorio()


def exportar_relatorio_csv():
    """Exporta os pedidos atualmente filtrados para um arquivo CSV."""
    pedidos = obter_pedidos_filtrados_relatorio()
    if not pedidos:
        messagebox.showinfo("Exportar", "Nenhum pedido no período para exportar.")
        return
    default_name = datetime.now().strftime("relatorio_%Y%m%d_%H%M%S.csv")
    caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=default_name)
    if not caminho:
        return
    try:
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Numero", "Data/Hora", "Cliente", "Item", "Total", "Pagamento", "Status"])
            for p in pedidos:
                writer.writerow([p["numero"], p["data_hora_str"], p["cliente"], p["item"], f"{p['total']:.2f}", p["pagamento"], p["status"]])
        messagebox.showinfo("Exportar", f"Relatório exportado em:\n{caminho}")
    except Exception as e:
        messagebox.showerror("Exportar", f"Erro ao exportar CSV:\n{e}")


def limpar_filtro_data():
    global filtro_inicio_data, filtro_fim_data
    filtro_inicio_data = None
    filtro_fim_data = None
    if ent_data_inicio is not None:
        ent_data_inicio.delete(0, END)
    if ent_data_fim is not None:
        ent_data_fim.delete(0, END)
    atualizar_relatorio()


def fechar_relatorio():
    global janela_relatorio
    global lbl_faturamento_bruto, lbl_faturamento_liquido, lbl_total_cancelado, lbl_qtd_pedidos, lbl_ticket_medio
    global ent_data_inicio, ent_data_fim, canvas_grafico, canvas_grafico_receita
    janela_relatorio.destroy()
    janela_relatorio = None
    lbl_faturamento_bruto = None
    lbl_faturamento_liquido = None
    lbl_total_cancelado = None
    lbl_qtd_pedidos = None
    lbl_ticket_medio = None
    ent_data_inicio = None
    ent_data_fim = None
    canvas_grafico = None
    canvas_grafico_receita = None


def abrir_relatorio_vendas():
    global janela_relatorio
    global lbl_faturamento_bruto, lbl_faturamento_liquido, lbl_total_cancelado, lbl_qtd_pedidos, lbl_ticket_medio
    global ent_data_inicio, ent_data_fim, canvas_grafico, canvas_grafico_receita

    if janela_relatorio is not None and janela_relatorio.winfo_exists():
        janela_relatorio.lift()
        atualizar_relatorio()
        return

    janela_relatorio = Toplevel(root)
    janela_relatorio.title("PizzaLoop - Relatórios")
    janela_relatorio.geometry("940x640")
    janela_relatorio.configure(bg=COR_BG)
    janela_relatorio.protocol("WM_DELETE_WINDOW", fechar_relatorio)

    topo = Frame(janela_relatorio, bg=COR_CARD, bd=1, relief="solid", highlightthickness=0)
    topo.pack(fill="x", padx=16, pady=(14, 8))
    Label(
        topo, text="Relatório de vendas", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 15, "bold")
    ).pack(side=LEFT, padx=12, pady=12)

    corpo = Frame(janela_relatorio, bg=COR_BG)
    corpo.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    filtro = LabelFrame(corpo, text="Filtros", bg=COR_CARD, fg=COR_MUTED, padx=10, pady=10)
    filtro.pack(fill="x")

    Label(filtro, text="Data inicial", bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=0, sticky="w")
    ent_data_inicio = Entry(filtro, width=14, relief="solid")
    ent_data_inicio.grid(row=1, column=0, padx=(0, 10), pady=(4, 0))

    Label(filtro, text="Data final", bg=COR_CARD, fg=COR_TEXTO).grid(row=0, column=1, sticky="w")
    ent_data_fim = Entry(filtro, width=14, relief="solid")
    ent_data_fim.grid(row=1, column=1, padx=(0, 10), pady=(4, 0))

    # Preencher datas padrão (últimos 7 dias) ao abrir o relatório
    try:
        hoje = datetime.now().date()
        inicio_padrao = hoje - timedelta(days=7)
        ent_data_inicio.insert(0, inicio_padrao.strftime("%d/%m/%Y"))
        ent_data_fim.insert(0, hoje.strftime("%d/%m/%Y"))
        aplicar_filtro_data()
    except Exception:
        pass

    Button(
        filtro, text="Aplicar", command=aplicar_filtro_data, bg=COR_PRIMARIA, fg="white", bd=0, padx=10
    ).grid(row=1, column=2, padx=4)
    Button(
        filtro, text="Limpar", command=limpar_filtro_data, bg="#94a3b8", fg="white", bd=0, padx=10
    ).grid(row=1, column=3, padx=4)
    Button(
        filtro, text="Exportar CSV", command=exportar_relatorio_csv, bg="#10b981", fg="white", bd=0, padx=10
    ).grid(row=1, column=4, padx=4)

    kpis = Frame(corpo, bg=COR_BG)
    kpis.pack(fill="x", pady=10)

    lbl_faturamento_bruto = Label(kpis, text="Faturamento bruto: R$ 0.00", bg=COR_BG, fg=COR_TEXTO, font=("Arial", 11, "bold"))
    lbl_faturamento_bruto.pack(anchor="w")
    lbl_faturamento_liquido = Label(kpis, text="Faturamento líquido: R$ 0.00", bg=COR_BG, fg=COR_TEXTO, font=("Arial", 11, "bold"))
    lbl_faturamento_liquido.pack(anchor="w")
    lbl_total_cancelado = Label(kpis, text="Total cancelado: R$ 0.00", bg=COR_BG, fg="#b91c1c", font=("Arial", 11, "bold"))
    lbl_total_cancelado.pack(anchor="w")
    lbl_qtd_pedidos = Label(kpis, text="Pedidos no período: 0", bg=COR_BG, fg=COR_TEXTO, font=("Arial", 11, "bold"))
    lbl_qtd_pedidos.pack(anchor="w")
    lbl_ticket_medio = Label(kpis, text="Ticket médio (sem cancelados): R$ 0.00", bg=COR_BG, fg=COR_TEXTO, font=("Arial", 11, "bold"))
    lbl_ticket_medio.pack(anchor="w")

    graficos = Frame(corpo, bg=COR_BG)
    graficos.pack(fill="both", expand=True)

    grafico_status_card = Frame(graficos, bg=COR_CARD, bd=1, relief="solid")
    grafico_status_card.pack(side=LEFT, fill="both", expand=True, padx=(0, 8), pady=4)
    Label(grafico_status_card, text="Pedidos por status", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
    canvas_grafico = Canvas(grafico_status_card, width=520, height=250, bg="#f8fafc", highlightthickness=0)
    canvas_grafico.pack(padx=10, pady=(0, 10), anchor="w")

    grafico_receita_card = Frame(graficos, bg=COR_CARD, bd=1, relief="solid")
    grafico_receita_card.pack(side=LEFT, fill="both", expand=True, pady=4)
    Label(grafico_receita_card, text="Receita e forma de pagamento", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
    canvas_grafico_receita = Canvas(grafico_receita_card, width=400, height=250, bg="#f8fafc", highlightthickness=0)
    canvas_grafico_receita.pack(padx=10, pady=(0, 10), anchor="w")

    atualizar_relatorio()


def obter_metricas_dashboard():
    qtd = len(pedidos_dados)
    total = sum(p["total"] for p in pedidos_dados)
    ticket = total / qtd if qtd else 0
    clientes_ativos = len(set(p["cliente"] for p in pedidos_dados))

    status_counts = {status: 0 for status in STATUS_OPCOES}
    for pedido in pedidos_dados:
        status = pedido["status"]
        if status in status_counts:
            status_counts[status] += 1

    pizzas_counts = {}
    for pedido in pedidos_dados:
        item = pedido["item"]
        pizzas_counts[item] = pizzas_counts.get(item, 0) + 1

    pagamentos_totais = {}
    for pedido in pedidos_dados:
        pagamento = pedido["pagamento"]
        pagamentos_totais[pagamento] = pagamentos_totais.get(pagamento, 0.0) + pedido["total"]

    pedidos_recentes = sorted(
        pedidos_dados, key=lambda p: p["data_hora_obj"], reverse=True
    )[:5]
    pizzas_mais_vendidas = sorted(
        pizzas_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    pagamentos_ordenados = sorted(
        pagamentos_totais.items(), key=lambda x: x[1], reverse=True
    )

    return {
        "qtd": qtd,
        "total": total,
        "ticket": ticket,
        "clientes_ativos": clientes_ativos,
        "status_counts": status_counts,
        "pedidos_recentes": pedidos_recentes,
        "pizzas_mais_vendidas": pizzas_mais_vendidas,
        "pagamentos_ordenados": pagamentos_ordenados,
    }


def preencher_lista_dashboard(frame, titulo_linha, linhas, vazio="Sem dados"):
    for widget in frame.winfo_children():
        widget.destroy()

    if not linhas:
        Label(frame, text=vazio, bg=COR_CARD, fg=COR_MUTED, font=("Arial", 9)).pack(anchor="w", pady=4)
        return

    for texto in linhas:
        Label(frame, text=texto, bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 9)).pack(
            anchor="w", pady=2
        )


def desenhar_grafico_dashboard_status(status_counts):
    if dash_canvas_status is None:
        return
    dash_canvas_status.delete("all")

    dados = [
        ("Novo", status_counts.get("Novo", 0), "#f59e0b"),
        ("Em preparo", status_counts.get("Em preparo", 0), "#3b82f6"),
        ("Rota", status_counts.get("Saiu para entrega", 0), "#a855f7"),
        ("Entregue", status_counts.get("Entregue", 0), "#22c55e"),
        ("Cancelado", status_counts.get("Cancelado", 0), "#ef4444"),
    ]
    max_valor = max(1, max(valor for _, valor, _ in dados))
    x = 20
    base = 175
    largura = 90
    for nome, valor, cor in dados:
        altura = int((valor / max_valor) * 120)
        y1 = base - altura
        dash_canvas_status.create_rectangle(x, y1, x + largura, base, fill=cor, outline="")
        dash_canvas_status.create_text(x + 45, y1 - 10, text=str(valor), fill=COR_TEXTO)
        dash_canvas_status.create_text(x + 45, base + 14, text=nome, fill=COR_MUTED, font=("Arial", 8, "bold"))
        x += 105


def atualizar_dashboard():
    if janela_dashboard is None or not janela_dashboard.winfo_exists():
        return

    metricas = obter_metricas_dashboard()
    dash_lbl_total_vendas.config(text=f"Vendas hoje\nR$ {metricas['total']:.2f}")
    dash_lbl_qtd_pedidos.config(text=f"Pedidos hoje\n{metricas['qtd']}")
    dash_lbl_ticket_medio.config(text=f"Ticket médio\nR$ {metricas['ticket']:.2f}")
    dash_lbl_clientes.config(text=f"Clientes ativos\n{metricas['clientes_ativos']}")

    linhas_recentes = []
    for pedido in metricas["pedidos_recentes"]:
        linhas_recentes.append(
            f"#{pedido['numero']} - {pedido['cliente']} | {pedido['item']} | R$ {pedido['total']:.2f}"
        )
    preencher_lista_dashboard(dash_frame_recentes, "Pedidos recentes", linhas_recentes)

    linhas_vendidas = []
    for i, (pizza, qtd) in enumerate(metricas["pizzas_mais_vendidas"], start=1):
        linhas_vendidas.append(f"{i}. {pizza} - {qtd} pedido(s)")
    preencher_lista_dashboard(dash_frame_mais_vendidas, "Mais vendidas", linhas_vendidas)

    for widget in dash_frame_pagamentos.winfo_children():
        widget.destroy()
    total_pagamentos = sum(valor for _, valor in metricas["pagamentos_ordenados"])
    if total_pagamentos == 0:
        Label(
            dash_frame_pagamentos,
            text="Sem pagamentos registrados.",
            bg=COR_CARD,
            fg=COR_MUTED,
            font=("Arial", 9),
        ).pack(anchor="w")
    else:
        for meio, valor in metricas["pagamentos_ordenados"]:
            pct = (valor / total_pagamentos) * 100 if total_pagamentos else 0
            linha = Frame(dash_frame_pagamentos, bg=COR_CARD)
            linha.pack(fill="x", pady=3)
            Label(linha, text=meio, bg=COR_CARD, fg=COR_TEXTO, width=14, anchor="w").pack(side=LEFT)
            barra = Canvas(linha, width=240, height=10, bg="#e5e7eb", highlightthickness=0)
            barra.pack(side=LEFT, padx=8)
            barra.create_rectangle(0, 0, int((pct / 100) * 240), 10, fill=COR_PRIMARIA, outline="")
            Label(linha, text=f"R$ {valor:.2f} ({pct:.1f}%)", bg=COR_CARD, fg=COR_MUTED, anchor="w").pack(side=LEFT)

    desenhar_grafico_dashboard_status(metricas["status_counts"])


def fechar_dashboard():
    global janela_dashboard
    global dash_lbl_total_vendas, dash_lbl_qtd_pedidos, dash_lbl_ticket_medio, dash_lbl_clientes
    global dash_canvas_status, dash_frame_recentes, dash_frame_mais_vendidas, dash_frame_pagamentos
    janela_dashboard.destroy()
    janela_dashboard = None
    dash_lbl_total_vendas = None
    dash_lbl_qtd_pedidos = None
    dash_lbl_ticket_medio = None
    dash_lbl_clientes = None
    dash_canvas_status = None
    dash_frame_recentes = None
    dash_frame_mais_vendidas = None
    dash_frame_pagamentos = None


def abrir_dashboard():
    global janela_dashboard
    global dash_lbl_total_vendas, dash_lbl_qtd_pedidos, dash_lbl_ticket_medio, dash_lbl_clientes
    global dash_canvas_status, dash_frame_recentes, dash_frame_mais_vendidas, dash_frame_pagamentos

    if janela_dashboard is not None and janela_dashboard.winfo_exists():
        janela_dashboard.lift()
        atualizar_dashboard()
        return

    janela_dashboard = Toplevel(root)
    janela_dashboard.title("PizzaLoop - Dashboard")
    janela_dashboard.geometry("1200x760")
    janela_dashboard.configure(bg=COR_BG)
    janela_dashboard.protocol("WM_DELETE_WINDOW", fechar_dashboard)

    topo = Frame(janela_dashboard, bg=COR_BG)
    topo.pack(fill="x", padx=16, pady=(14, 8))
    Label(topo, text="Dashboard", bg=COR_BG, fg=COR_TEXTO, font=("Arial", 20, "bold")).pack(anchor="w")
    Label(topo, text="Visão geral operacional", bg=COR_BG, fg=COR_MUTED, font=("Arial", 10)).pack(anchor="w")

    cards = Frame(janela_dashboard, bg=COR_BG)
    cards.pack(fill="x", padx=16, pady=(0, 10))

    def criar_card(parent):
        card = Frame(parent, bg=COR_CARD, bd=1, relief="solid", padx=12, pady=10)
        card.pack(side=LEFT, fill="x", expand=True, padx=4)
        return card

    c1 = criar_card(cards)
    c2 = criar_card(cards)
    c3 = criar_card(cards)
    c4 = criar_card(cards)
    dash_lbl_total_vendas = Label(c1, text="Vendas hoje\nR$ 0.00", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 12, "bold"), justify=LEFT)
    dash_lbl_total_vendas.pack(anchor="w")
    dash_lbl_qtd_pedidos = Label(c2, text="Pedidos hoje\n0", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 12, "bold"), justify=LEFT)
    dash_lbl_qtd_pedidos.pack(anchor="w")
    dash_lbl_ticket_medio = Label(c3, text="Ticket médio\nR$ 0.00", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 12, "bold"), justify=LEFT)
    dash_lbl_ticket_medio.pack(anchor="w")
    dash_lbl_clientes = Label(c4, text="Clientes ativos\n0", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 12, "bold"), justify=LEFT)
    dash_lbl_clientes.pack(anchor="w")

    meio = Frame(janela_dashboard, bg=COR_BG)
    meio.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    card_recentes = Frame(meio, bg=COR_CARD, bd=1, relief="solid")
    card_recentes.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))
    Label(card_recentes, text="Pedidos Recentes", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
    dash_frame_recentes = Frame(card_recentes, bg=COR_CARD)
    dash_frame_recentes.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    card_vendidas = Frame(meio, bg=COR_CARD, bd=1, relief="solid")
    card_vendidas.pack(side=LEFT, fill="both", expand=True)
    Label(card_vendidas, text="Mais Vendidas", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
    dash_frame_mais_vendidas = Frame(card_vendidas, bg=COR_CARD)
    dash_frame_mais_vendidas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    base = Frame(janela_dashboard, bg=COR_BG)
    base.pack(fill="x", padx=16, pady=(0, 16))

    card_graf = Frame(base, bg=COR_CARD, bd=1, relief="solid")
    card_graf.pack(side=LEFT, fill="x", expand=True, padx=(0, 8))
    Label(card_graf, text="Status dos Pedidos", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
    dash_canvas_status = Canvas(card_graf, width=560, height=210, bg="#f8fafc", highlightthickness=0)
    dash_canvas_status.pack(padx=10, pady=(0, 10), anchor="w")

    card_pag = Frame(base, bg=COR_CARD, bd=1, relief="solid")
    card_pag.pack(side=LEFT, fill="x", expand=True)
    Label(card_pag, text="Métodos de Pagamento", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
    dash_frame_pagamentos = Frame(card_pag, bg=COR_CARD)
    dash_frame_pagamentos.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    atualizar_dashboard()


def abrir_modulo(nome):
    if nome == "Dashboard":
        abrir_dashboard()
    elif nome == "Pedidos":
        messagebox.showinfo("Pedidos", "Você já está no módulo de pedidos.")
    elif nome == "Cardápio":
        messagebox.showinfo("Cardápio", "Use os botões de pizza para seleção.")
    elif nome == "Relatórios":
        abrir_relatorio_vendas()
    elif nome == "Clientes":
        messagebox.showinfo("Clientes", "Cadastro e lista já disponíveis neste painel.")


root = Tk()
root.title("PizzaLoop - Gerenciar pedidos")
root.geometry("1450x880")
root.configure(bg=COR_BG)

item_selecionado = StringVar(value="Nenhum item selecionado")
preco_selecionado = DoubleVar(value=0.0)

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Custom.Treeview",
    background="#fffdfa",
    fieldbackground="#fffdfa",
    foreground="#0f172a",
    rowheight=34,
    bordercolor="#e4c8b5",
    borderwidth=1,
    relief="flat",
)
style.configure(
    "Custom.Treeview.Heading",
    background="#f8fafc",
    foreground="#0f172a",
    font=("Arial", 10, "bold"),
    bordercolor="#d9a066",
    borderwidth=1,
)
style.map(
    "Custom.Treeview",
    background=[("selected", "#fed7aa")],
    foreground=[("selected", "#0f172a")],
)

layout = Frame(root, bg=COR_BG)
layout.pack(fill="both", expand=True)

# Sidebar
sidebar = Frame(layout, bg=COR_SIDEBAR, width=220)
sidebar.pack(side=LEFT, fill="y")
sidebar.pack_propagate(False)

logo = Frame(sidebar, bg=COR_SIDEBAR)
logo.pack(fill="x", padx=14, pady=14)
Label(logo, text="PizzaLoop", bg=COR_SIDEBAR, fg="white", font=("Arial", 16, "bold")).pack(anchor="w")
Label(logo, text="Painel administrativo", bg=COR_SIDEBAR, fg=COR_SIDEBAR_TXT, font=("Arial", 9)).pack(anchor="w")

for item in ["Dashboard", "Pedidos", "Cardápio", "Relatórios", "Clientes"]:
    cor = COR_PRIMARIA if item == "Pedidos" else COR_SIDEBAR
    item_sidebar = Label(
        sidebar,
        text=f"  {item}",
        bg=cor,
        fg="white",
        font=("Arial", 10, "bold"),
        pady=10,
        cursor="hand2",
    )
    item_sidebar.pack(fill="x", padx=8, pady=2)
    item_sidebar.bind("<Button-1>", lambda _event, n=item: abrir_modulo(n))
    sidebar.bindtags((sidebar,) + sidebar.bindtags())

# Conteúdo principal
main = Frame(layout, bg=COR_BG)
main.pack(side=LEFT, fill="both", expand=True)

header = Frame(main, bg=COR_BG)
header.pack(fill="x", padx=18, pady=(16, 10))
Label(header, text="Gerenciar Pedidos", bg=COR_BG, fg=COR_TEXTO, font=("Arial", 20, "bold")).pack(anchor="w")
Label(header, text="Visualize e gerencie todos os pedidos", bg=COR_BG, fg=COR_MUTED, font=("Arial", 10)).pack(anchor="w")

toolbar = Frame(main, bg=COR_CARD, bd=1, relief="solid")
toolbar.pack(fill="x", padx=18, pady=(0, 8))

ent_busca = Entry(toolbar, relief="flat", font=("Arial", 10))
ent_busca.insert(0, "")
ent_busca.pack(side=LEFT, fill="x", expand=True, padx=12, pady=10, ipady=5)
Button(toolbar, text="Buscar", command=filtrar_pedidos, bg="#e2e8f0", fg=COR_TEXTO, bd=0, padx=12).pack(side=LEFT, padx=(0, 8))

botoes_status = {}
for status in ["Todos", "Novo", "Em preparo", "Saiu para entrega", "Entregue", "Cancelado"]:
    botao = Button(
        toolbar,
        text=status,
        command=lambda s=status: alterar_filtro_status(s),
        bg=COR_PRIMARIA if status == "Todos" else "#f1f5f9",
        fg="white" if status == "Todos" else COR_TEXTO,
        bd=0,
        padx=8,
        pady=6,
        font=("Arial", 9, "bold"),
        cursor="hand2",
    )
    botao.pack(side=LEFT, padx=3, pady=8)
    botoes_status[status] = botao

corpo = Frame(main, bg=COR_BG)
corpo.pack(fill="both", expand=True, padx=18, pady=(0, 10))

top_cards = Frame(corpo, bg=COR_BG)
top_cards.pack(fill="x", pady=(0, 8))

frame_menu = LabelFrame(top_cards, text="Cardápio", bg=COR_CARD, fg=COR_MUTED, bd=1, relief="solid", padx=8, pady=8)
frame_menu.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))

frame_form = LabelFrame(top_cards, text="Novo pedido", bg=COR_CARD, fg=COR_MUTED, bd=1, relief="solid", padx=10, pady=8)
frame_form.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))

frame_clientes = LabelFrame(top_cards, text="Clientes", bg=COR_CARD, fg=COR_MUTED, bd=1, relief="solid", padx=10, pady=8)
frame_clientes.pack(side=LEFT, fill="both", expand=True)

for i, (nome, sabor, preco) in enumerate(PIZZAS):
    Button(
        frame_menu,
        text=f"{nome} - {sabor} | R$ {preco:.2f}",
        command=lambda n=nome, s=sabor, p=preco: selecionar_item(n, s, p),
        bg="#fff7ed",
        fg=COR_TEXTO,
        activebackground="#ffedd5",
        bd=0,
        font=("Arial", 9, "bold"),
        pady=4,
        cursor="hand2",
    ).grid(row=i, column=0, sticky="ew", pady=2)
frame_menu.grid_columnconfigure(0, weight=1)

Label(frame_form, text="Cliente", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
ent_cliente = Entry(frame_form, relief="solid")
ent_cliente.grid(row=1, column=0, sticky="ew", pady=(2, 6))

Label(frame_form, text="Pagamento", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w")
cmb_pagamento = ttk.Combobox(frame_form, values=PAGAMENTOS, state="readonly")
cmb_pagamento.grid(row=3, column=0, sticky="ew", pady=(2, 6))

lbl_item = Label(frame_form, text="Item: Nenhum item selecionado", bg=COR_CARD, fg=COR_MUTED, font=("Arial", 9, "bold"))
lbl_item.grid(row=4, column=0, sticky="w")
lbl_total = Label(frame_form, text="Total: R$ 0.00", bg=COR_CARD, fg="#16a34a", font=("Arial", 10, "bold"))
lbl_total.grid(row=5, column=0, sticky="w", pady=(0, 6))

Button(frame_form, text="Registrar pedido", command=registrar_pedido, bg=COR_PRIMARIA, fg="white", bd=0, pady=8, cursor="hand2").grid(row=6, column=0, sticky="ew", pady=(4, 4))
Button(frame_form, text="Limpar", command=limpar_formulario, bg="#94a3b8", fg="white", bd=0, pady=8, cursor="hand2").grid(row=7, column=0, sticky="ew")
frame_form.grid_columnconfigure(0, weight=1)

Label(frame_clientes, text="Novo cliente", bg=COR_CARD, fg=COR_TEXTO, font=("Arial", 9, "bold")).pack(anchor="w")
ent_novo_cliente = Entry(frame_clientes, relief="solid")
ent_novo_cliente.pack(fill="x", pady=(2, 6))
Button(frame_clientes, text="Cadastrar cliente", command=cadastrar_cliente, bg=COR_PRIMARIA, fg="white", bd=0, cursor="hand2").pack(fill="x")
Button(frame_clientes, text="Remover cliente", command=remover_cliente, bg="#b91c1c", fg="white", bd=0, cursor="hand2").pack(fill="x", pady=(6, 0))

frame_lista_clientes_container = Frame(frame_clientes, bg=COR_CARD, height=260)
frame_lista_clientes_container.pack(fill="both", expand=True, pady=(8, 0))
frame_lista_clientes_container.pack_propagate(False)

canvas_clientes = Canvas(frame_lista_clientes_container, bg=COR_CARD, highlightthickness=0)
scrollbar_clientes = Scrollbar(frame_lista_clientes_container, orient=VERTICAL, command=canvas_clientes.yview)
frame_lista_clientes = Frame(canvas_clientes, bg=COR_CARD)

canvas_clientes.configure(yscrollcommand=scrollbar_clientes.set)
scrollbar_clientes.pack(side=RIGHT, fill=Y)
canvas_clientes.pack(side=LEFT, fill="both", expand=True)
canvas_clientes.create_window((0, 0), window=frame_lista_clientes, anchor="nw")

frame_lista_clientes.bind(
    "<Configure>",
    lambda event: canvas_clientes.configure(scrollregion=canvas_clientes.bbox("all")),
)

card_tabela = Frame(corpo, bg=COR_CARD, bd=1, relief="solid")
card_tabela.pack(fill="both", expand=True)

topo_tabela = Frame(card_tabela, bg=COR_CARD)
topo_tabela.pack(fill="x", padx=10, pady=(8, 4))
lbl_count = Label(topo_tabela, text="Mostrando 0 pedido(s)", bg=COR_CARD, fg=COR_MUTED, font=("Arial", 9))
lbl_count.pack(side=LEFT)

colunas = ("pedido", "data_hora", "cliente", "item", "total", "pagamento", "status", "acoes")
tabela = ttk.Treeview(card_tabela, columns=colunas, show="headings", height=9, style="Custom.Treeview")
tabela.heading("pedido", text="Pedido", anchor=CENTER)
tabela.heading("data_hora", text="Data/Hora", anchor=CENTER)
tabela.heading("cliente", text="Cliente", anchor=CENTER)
tabela.heading("item", text="Item", anchor=CENTER)
tabela.heading("total", text="Total", anchor=CENTER)
tabela.heading("pagamento", text="Pagamento", anchor=CENTER)
tabela.heading("status", text="Status", anchor=CENTER)
tabela.heading("acoes", text="Ações", anchor=CENTER)
tabela.column("pedido", width=85, anchor=CENTER)
tabela.column("data_hora", width=120, anchor=CENTER)
tabela.column("cliente", width=140, anchor=CENTER)
tabela.column("item", width=240, anchor=CENTER)
tabela.column("total", width=90, anchor=CENTER)
tabela.column("pagamento", width=95, anchor=CENTER)
tabela.column("status", width=120, anchor=CENTER)
tabela.column("acoes", width=130, anchor=CENTER)
tabela.pack(fill="both", expand=True, padx=10, pady=6)

# Cores de status na tabela
tabela.tag_configure("Novo", foreground="#92400e")
tabela.tag_configure("Em preparo", foreground="#1d4ed8")
tabela.tag_configure("Saiu para entrega", foreground="#7c3aed")
tabela.tag_configure("Entregue", foreground="#15803d")
tabela.tag_configure("Cancelado", foreground="#dc2626")

acoes = Frame(card_tabela, bg=COR_CARD)
acoes.pack(fill="x", padx=10, pady=(2, 10))
Button(acoes, text="Em preparo", command=lambda: alterar_status("Em preparo"), bg="#3b82f6", fg="white", bd=0, padx=12, pady=8, cursor="hand2").pack(side=LEFT, padx=(0, 6))
Button(acoes, text="Saiu para entrega", command=lambda: alterar_status("Saiu para entrega"), bg="#8b5cf6", fg="white", bd=0, padx=12, pady=8, cursor="hand2").pack(side=LEFT, padx=(0, 6))
Button(acoes, text="Entregue", command=lambda: alterar_status("Entregue"), bg="#16a34a", fg="white", bd=0, padx=12, pady=8, cursor="hand2").pack(side=LEFT, padx=(0, 6))
Button(acoes, text="Cancelado", command=lambda: alterar_status("Cancelado"), bg="#dc2626", fg="white", bd=0, padx=12, pady=8, cursor="hand2").pack(side=LEFT, padx=(0, 6))
Button(acoes, text="Excluir pedido", command=excluir_pedido, bg="#64748b", fg="white", bd=0, padx=12, pady=8, cursor="hand2").pack(side=LEFT)

mensagem_status = Label(root, text="Sistema PizzaLoop pronto.", bg=COR_BG, fg=COR_MUTED, font=("Arial", 10, "bold"))
mensagem_status.pack(fill="x", padx=18, pady=(0, 8))

aplicar_filtro_tabela()
root.mainloop()
