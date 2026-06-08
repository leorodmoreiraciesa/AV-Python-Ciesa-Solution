# AV-Python-Ciesa-Solution
A Ciesa Solutions é uma empresa de tecnologia com mais de 300 clientes corporativos que contratam

suporte técnico mensal. Atualmente, o controle de chamados é feito em planilhas — um processo lento

e sujeito a erros. A empresa perdeu contratos recentemente por descumprir o SLA sem perceber que

havia chamados críticos em aberto.


O trio foi contratado para desenvolver o HelpDesk Pro: um sistema interno de gestão de chamados

construído em Python com Orientação a Objetos e exposto via uma API REST com Flask, permitindo

integração com outros sistemas da empresa.


Requisito crítico da Ciesa Solutions: O sistema deve localizar qualquer chamado pelo número
em tempo constante, mesmo com milhares de registros. O gerente técnico (professor) espera que o trio saiba justificar a escolha da estrutura de dados usada para isso.

Estrutura Orientada a Objetos
Classes:
Chamado
           Atributos:

                - numero
                - titulo
                - descricao
                - cliente
                - prioridade (baixa, media, alta, critica)
                - status
                - data_abertura 
                - sla_horas 
                - tecnico
                - historico
    
             Métodos:
                 •  _init_(titulo, descricao, cliente, prioridade) — Gera número sequencial, define status 'aberto', data_abertura=agora, calcula sla_horas. Lança ValueError se prioridade inválida.

                  • _str_() — Linha resumida: número, título, cliente, prioridade, status e tempo decorrido.

                  • tempo_decorrido() — Retorna datetime.timedelta desde a abertura.

                  • esta_em_atraso() — True se o tempo decorrido ultrapassar sla_horas e status não for 'resolvido'/'fechado'.

                  • registrar_acao(acao, responsavel) — Adiciona entrada em historico com data atual, ação e responsável.

                  • alterar_status(novo_status, responsavel) — Muda o status validando transições permitidas. Registra no histórico. Transições válidas: aberto→em_atendimento→aguardando_cliente→em_atendimento→resolvido→fechado.

                   • to_dict() — Retorna dicionário com todos os atributos serializáveis (datas como string ISO). Usado pela API Flask.

Tecnico
             Atributos:
                - id_tecnico 
                - nome
                - especialidades
                - chamados_ativos 
                - capacidade_maxima
                - disponivel : True se len(chamados_ativos) < capacidade_maxima.

              Métodos:
                  • _init(nome, especialidades, capacidade_maxima=5) — especialidades convertido para set internamente.• __str_() — Nome, especialidades, chamados ativos e disponibilidade.

                  • atribuir_chamado(numero) — Adiciona à lista e atualiza disponivel. Lança CapacidadeExcedidaException se no limite.

                  • liberar_chamado(numero) — Remove da lista e atualiza disponivel. Lança ValueError se não encontrado.

                  • tem_especialidade(categoria) — True se a categoria estiver no set especialidades.

                  • to_dict() — Retorna dicionário serializável para uso na API Flask.

CentralDeSupporte
             Atributos:
                - empresa 
                - chamados
                - tecnicos
                - fila_nao_atribuidos 
               
               Métodos:
                  • _init_(empresa) — Inicializa dicionários vazios e fila vazia.
                  • abrir_chamado(titulo, descricao, cliente, prioridade) — Cria Chamado, armazena em chamados e adiciona à fila_nao_atribuidos. Retorna o objeto.
                  • registrar_tecnico(nome, especialidades, capacidade_maxima=5) — Cria Tecnico, armazena e retorna o objeto.
                  • buscar_chamado(numero) — Retorna o Chamado pelo número. Lança ChamadoNaoEncontradoException se inexistente.
                  • atribuir_tecnico(numero_chamado, id_tecnico) — Vincula técnico ao chamado, remove da fila, muda status para 'em_atendimento'.
                  • atribuicao_automatica() — Percorre a fila e atribui cada chamado ao técnico com menos chamados ativos. Retorna quantidade atribuída.
                  • resolver_chamado(numero, id_tecnico, descricao_solucao) — Status→'resolvido', registra solução no histórico, libera o técnico. Valida responsabilidade.
                 • fechar_chamado(numero) — Status 'resolvido'→'fechado'.
                 • listar_em_atraso() — Lista de chamados com esta_em_atraso()==True, do mais atrasado ao mais recente.
                 • relatorio_por_prioridade() — Dicionário agrupando chamados ativos por prioridade.
                 • painel_operacional() — Resumo: chamados por status, em atraso, técnicos disponíveis, top 3 clientes com mais chamados.


Regras de negócio obrigatórias
* SLA automático: Critica=4h, Alta=8h, Média=24h, Baixa=72h. Cálculo de atraso com datetime.
* Balanceamento de carga: atribuicao_automatica() escolhe o técnico com menos chamados
ativos. Empate: menor id.
* Transições de status:
aberto→em_atendimento→aguardando_cliente→em_atendimento→resolvido→fechado. Nenhuma
outra é permitida.
* Histórico completo: Toda alteração de status, atribuição e solução registra data, ação e
responsável.
* to_dict() obrigatório: Todas as classes devem implementar to_dict() retornando dicionário serializável para o JSON da API.

API

O sistema de classes deve ser exposto via uma API REST construída com Flask. Todas as rotas
devem retornar JSON. Erros devem retornar o código HTTP adequado e uma mensagem descritiva no
campo "erro".
Instancie a CentralDeSupporte uma única vez fora das rotas (variável global ou contexto da aplicação) para que o estado persista entre requisições durante a execução do servidor.
POST /chamados — Abre um novo chamado. Body: titulo, descricao, cliente, prioridade. Retorna 201 + JSON do chamado.
GET /chamados — Lista todos os chamados. Query param opcional: status. Retorna 200 + lista.
GET /chamados/<int:numero> — Busca chamado pelo número. Retorna 200 ou 404.
PATCH /chamados/<int:numero>/status — Altera status. Body: novo_status, responsavel. Retorna 200, 400 ou 404.
PATCH /chamados/<int:numero>/resolver — Resolve um chamado. Body: id_tecnico, descricao_solucao. Retorna 200, 400, 403 ou 404.
GET /chamados/em-atraso — Lista chamados em atraso, ordenados. Retorna 200.
POST /tecnicos — Registra novo técnico. Body: nome, especialidades, capacidade_maxima (opcional). Retorna 201.
GET /tecnicos — Lista técnicos. Query param opcional: disponivel=true/false. Retorna 200.
POST /atribuicao/automatica — Executa atribuição automática da fila. Retorna quantidade e lista de chamados atribuídos.
GET /painel — Retorna painel operacional: totais por status, em atraso, técnicos disponíveis, top 3 clientes.
Dica de implementação: Crie um arquivo app.py separado com as rotas Flask que importa as classes do arquivo principal. Use jsonify() para retornar JSON e request.get_json() para ler o body das requisições.
Cenário de demonstração obrigatório
Ao executar helpdesk_TRIO_NOMES.py diretamente (bloco if _name_ == '_main_':), o
script deve:
✔️ Criar a central 'Ciesa Solutions' e registrar ao menos 4 técnicos com especialidades variadas.
✔️ Abrir ao menos 8 chamados com prioridades e clientes diferentes.
✔️ Executar atribuicao_automatica() e exibir o resultado.
✔️ Simular a resolução de 2 chamados e o fechamento de 1.
✔️ Forçar uma transição de status inválida e tratar a exceção com mensagem amigável.
✔️ Simular um chamado em atraso e exibir listar_em_atraso().
✔️ Exibir o painel_operacional() ao final.

Arquivos de entrega
* helpdesk_TRIO_NOMES.py — Classes + bloco de demonstração
* app.py — Aplicação Flask com todos os endpoints
