import datetime
from collections import defaultdict

# --- Exceções Customizadas ---
class CapacidadeExcedidaException(Exception):
    pass

class ChamadoNaoEncontradoException(Exception):
    pass

# --- Classes Principais ---
class Chamado:
    _gerador_numero = 1
    SLA_MAP = {'critica': 4, 'alta': 8, 'media': 24, 'baixa': 72}
    STATUS_TRANSICOES = {
        'aberto': ['em_atendimento'],
        'em_atendimento': ['aguardando_cliente', 'resolvido'],
        'aguardando_cliente': ['em_atendimento'],
        'resolvido': ['fechado'],
        'fechado': []
    }

    def __init__(self, titulo, descricao, cliente, prioridade):
        prioridade = prioridade.lower()
        if prioridade not in self.SLA_MAP:
            raise ValueError("Prioridade inválida. Use: baixa, media, alta, critica.")
        
        self.numero = Chamado._gerador_numero
        Chamado._gerador_numero += 1
        
        self.titulo = titulo
        self.descricao = descricao
        self.cliente = cliente
        self.prioridade = prioridade
        self.status = 'aberto'
        self.data_abertura = datetime.datetime.now()
        self.sla_horas = self.SLA_MAP[prioridade]
        self.tecnico = None
        self.historico = []
        
        self.registrar_acao("Abertura do chamado", "Sistema")

    def __str__(self):
        return f"[#{self.numero}] {self.titulo} - {self.cliente} | Prioridade: {self.prioridade.upper()} | Status: {self.status.upper()} | Tempo: {self.tempo_decorrido()}"

    def tempo_decorrido(self):
        return datetime.datetime.now() - self.data_abertura

    def esta_em_atraso(self):
        if self.status in ['resolvido', 'fechado']:
            return False
        return self.tempo_decorrido() > datetime.timedelta(hours=self.sla_horas)

    def registrar_acao(self, acao, responsavel):
        self.historico.append({
            'data': datetime.datetime.now().isoformat(),
            'acao': acao,
            'responsavel': responsavel
        })

    def alterar_status(self, novo_status, responsavel):
        novo_status = novo_status.lower()
        if novo_status not in self.STATUS_TRANSICOES.get(self.status, []):
            raise ValueError(f"Transição inválida: {self.status} -> {novo_status}")
        
        self.status = novo_status
        self.registrar_acao(f"Status alterado para {novo_status}", responsavel)

    def to_dict(self):
        return {
            'numero': self.numero,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'cliente': self.cliente,
            'prioridade': self.prioridade,
            'status': self.status,
            'data_abertura': self.data_abertura.isoformat(),
            'sla_horas': self.sla_horas,
            'tecnico': self.tecnico,
            'em_atraso': self.esta_em_atraso(),
            'historico': self.historico
        }

class Tecnico:
    _gerador_id = 1

    def __init__(self, nome, especialidades, capacidade_maxima=5):
        self.id_tecnico = Tecnico._gerador_id
        Tecnico._gerador_id += 1
        
        self.nome = nome
        self.especialidades = set(especialidades)
        self.chamados_ativos = []
        self.capacidade_maxima = capacidade_maxima
        self.disponivel = True

    def __str__(self):
        return f"Tecnico {self.nome} (ID: {self.id_tecnico}) | Chamados: {len(self.chamados_ativos)}/{self.capacidade_maxima} | Disp: {self.disponivel}"

    def atribuir_chamado(self, numero):
        if len(self.chamados_ativos) >= self.capacidade_maxima:
            raise CapacidadeExcedidaException(f"Técnico {self.nome} atingiu a capacidade máxima.")
        self.chamados_ativos.append(numero)
        self._atualizar_disponibilidade()

    def liberar_chamado(self, numero):
        if numero not in self.chamados_ativos:
            raise ValueError("Chamado não atribuído a este técnico.")
        self.chamados_ativos.remove(numero)
        self._atualizar_disponibilidade()

    def _atualizar_disponibilidade(self):
        self.disponivel = len(self.chamados_ativos) < self.capacidade_maxima

    def tem_especialidade(self, categoria):
        return categoria in self.especialidades

    def to_dict(self):
        return {
            'id_tecnico': self.id_tecnico,
            'nome': self.nome,
            'especialidades': list(self.especialidades),
            'chamados_ativos': self.chamados_ativos,
            'capacidade_maxima': self.capacidade_maxima,
            'disponivel': self.disponivel
        }

class CentralDeSupporte:
    def __init__(self, empresa):
        self.empresa = empresa
        self.chamados = {} # Dicionário para garantir busca O(1)
        self.tecnicos = {}
        self.fila_nao_atribuidos = []

    def abrir_chamado(self, titulo, descricao, cliente, prioridade):
        chamado = Chamado(titulo, descricao, cliente, prioridade)
        self.chamados[chamado.numero] = chamado
        self.fila_nao_atribuidos.append(chamado.numero)
        return chamado

    def registrar_tecnico(self, nome, especialidades, capacidade_maxima=5):
        tecnico = Tecnico(nome, especialidades, capacidade_maxima)
        self.tecnicos[tecnico.id_tecnico] = tecnico
        return tecnico

    def buscar_chamado(self, numero):
        if numero not in self.chamados:
            raise ChamadoNaoEncontradoException(f"Chamado #{numero} não encontrado.")
        return self.chamados[numero]

    def atribuir_tecnico(self, numero_chamado, id_tecnico):
        chamado = self.buscar_chamado(numero_chamado)
        tecnico = self.tecnicos.get(id_tecnico)
        if not tecnico:
            raise ValueError("Técnico não encontrado.")
        
        tecnico.atribuir_chamado(chamado.numero)
        chamado.tecnico = tecnico.id_tecnico
        
        if chamado.numero in self.fila_nao_atribuidos:
            self.fila_nao_atribuidos.remove(chamado.numero)
            
        chamado.alterar_status('em_atendimento', f"Tecnico ID: {id_tecnico}")

    def atribuicao_automatica(self):
        atribuidos = 0
        chamados_atribuidos_info = []
        
        # Filtra apenas técnicos disponíveis
        tecnicos_disp = [t for t in self.tecnicos.values() if t.disponivel]
        if not tecnicos_disp:
            return 0, []

        for numero_chamado in list(self.fila_nao_atribuidos):
            # Ordena por carga (menor primeiro) e empates pelo menor ID
            tecnicos_disp.sort(key=lambda t: (len(t.chamados_ativos), t.id_tecnico))
            
            tecnico_escolhido = tecnicos_disp[0]
            try:
                self.atribuir_tecnico(numero_chamado, tecnico_escolhido.id_tecnico)
                atribuidos += 1
                chamados_atribuidos_info.append(numero_chamado)
                if not tecnico_escolhido.disponivel:
                    tecnicos_disp.remove(tecnico_escolhido)
            except CapacidadeExcedidaException:
                pass
                
            if not tecnicos_disp:
                break # Sem técnicos disponíveis
                
        return atribuidos, chamados_atribuidos_info

    def resolver_chamado(self, numero, id_tecnico, descricao_solucao):
        chamado = self.buscar_chamado(numero)
        tecnico = self.tecnicos.get(id_tecnico)
        
        if chamado.tecnico != id_tecnico:
            raise PermissionError("Apenas o técnico responsável pode resolver o chamado.")
            
        chamado.alterar_status('resolvido', f"Tecnico ID: {id_tecnico}")
        chamado.registrar_acao(f"Solução: {descricao_solucao}", f"Tecnico ID: {id_tecnico}")
        tecnico.liberar_chamado(numero)

    def fechar_chamado(self, numero):
        chamado = self.buscar_chamado(numero)
        chamado.alterar_status('fechado', "Sistema/Admin")

    def listar_em_atraso(self):
        em_atraso = [c for c in self.chamados.values() if c.esta_em_atraso()]
        # Ordena do mais atrasado (data de abertura menor/mais antiga) ao mais recente
        em_atraso.sort(key=lambda c: c.data_abertura)
        return em_atraso

    def relatorio_por_prioridade(self):
        relatorio = defaultdict(list)
        for chamado in self.chamados.values():
            if chamado.status not in ['resolvido', 'fechado']:
                relatorio[chamado.prioridade].append(chamado.to_dict())
        return dict(relatorio)

    def painel_operacional(self):
        status_cont = defaultdict(int)
        em_atraso_cont = 0
        clientes_cont = defaultdict(int)
        
        for c in self.chamados.values():
            status_cont[c.status] += 1
            if c.esta_em_atraso():
                em_atraso_cont += 1
            clientes_cont[c.cliente] += 1
            
        tecnicos_disp = sum(1 for t in self.tecnicos.values() if t.disponivel)
        
        # Top 3 clientes
        top_clientes = sorted(clientes_cont.items(), key=lambda item: item[1], reverse=True)[:3]

        return {
            'totais_por_status': dict(status_cont),
            'chamados_em_atraso': em_atraso_cont,
            'tecnicos_disponiveis': tecnicos_disp,
            'top_3_clientes': top_clientes
        }

# --- Cenário de Demonstração ---
if __name__ == '__main__':
    print("--- INICIANDO DEMONSTRAÇÃO HELPDESK PRO ---")
    central = CentralDeSupporte("Ciesa Solutions")

    # 1. Registrar 4 Técnicos
    print("\n[+] Registrando Técnicos...")
    t1 = central.registrar_tecnico("Alice", ["Redes", "Hardware"])
    t2 = central.registrar_tecnico("Bruno", ["Software", "Banco de Dados"])
    t3 = central.registrar_tecnico("Carlos", ["Sistemas Operacionais"])
    t4 = central.registrar_tecnico("Diana", ["Redes", "Software"], capacidade_maxima=2)
    for t in central.tecnicos.values(): print(t)

    # 2. Abrir 8 chamados
    print("\n[+] Abrindo 8 Chamados...")
    clientes = ["Empresa A", "Empresa B", "Empresa C", "Empresa A"]
    central.abrir_chamado("Sem internet", "Roteador não responde", "Empresa A", "alta")
    central.abrir_chamado("Erro no ERP", "Sistema não loga", "Empresa B", "critica")
    central.abrir_chamado("Mouse quebrado", "Troca de mouse", "Empresa C", "baixa")
    central.abrir_chamado("Banco de dados lento", "Queries lentas", "Empresa A", "media")
    central.abrir_chamado("Servidor desligou", "Fonte queimada", "Empresa B", "critica")
    central.abrir_chamado("Instalação do Pacote Office", "Novo funcionário", "Empresa C", "baixa")
    central.abrir_chamado("Wi-fi caindo", "Oscilação", "Empresa D", "media")
    central.abrir_chamado("Erro 404 no site", "Portal fora do ar", "Empresa A", "alta")
    print(f"Chamados criados: {len(central.chamados)}")

    # 3. Atribuição Automática
    print("\n[+] Executando Atribuição Automática...")
    qnt, atribuidos = central.atribuicao_automatica()
    print(f"Chamados atribuídos: {qnt}. Lista: {atribuidos}")
    for t in central.tecnicos.values(): print(t)

    # 4. Simular resolução de 2 chamados e fechamento de 1
    print("\n[+] Resolvendo e Fechando chamados...")
    id_tecnico_chamado_1 = central.buscar_chamado(1).tecnico
    central.resolver_chamado(1, id_tecnico_chamado_1, "Cabo de rede reconectado.")
    print(f"Chamado 1 Status: {central.buscar_chamado(1).status}")
    
    id_tecnico_chamado_2 = central.buscar_chamado(2).tecnico
    central.resolver_chamado(2, id_tecnico_chamado_2, "Serviço de login reiniciado.")
    central.fechar_chamado(2)
    print(f"Chamado 2 Status: {central.buscar_chamado(2).status}")

    # 5. Forçar transição inválida
    print("\n[+] Tentativa de transição de status inválida...")
    try:
        # Tentar fechar um chamado que está 'em_atendimento' direto para 'fechado'
        central.buscar_chamado(3).alterar_status('fechado', "Admin")
    except ValueError as e:
        print(f"SUCESSO NO TRATAMENTO DE ERRO: {e}")

    # 6. Simular chamado em atraso
    print("\n[+] Simulando chamado em atraso...")
    # Forçar a data de abertura para 10 horas atrás para um chamado de SLA 4h (Crítica)
    chamado_atraso = central.buscar_chamado(5) # Chamado 5 é Crítica
    chamado_atraso.data_abertura = datetime.datetime.now() - datetime.timedelta(hours=10)
    
    atrasados = central.listar_em_atraso()
    for c in atrasados:
        print(f"EM ATRASO: {c}")

    # 7. Painel Operacional
    print("\n[+] Painel Operacional...")
    import json
    print(json.dumps(central.painel_operacional(), indent=2, ensure_ascii=False))

