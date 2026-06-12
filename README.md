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

# 🎫 HelpDesk Pro — Ciesa Solutions

> Sistema interno de gestão de chamados de suporte técnico, desenvolvido em Python com Orientação a Objetos e exposto via API REST com Flask.

---

## 📋 Contexto

A **Ciesa Solutions** é uma empresa de tecnologia com mais de 300 clientes corporativos que contratam suporte técnico mensal. O controle de chamados era feito em planilhas — um processo lento e sujeito a erros — e a empresa chegou a perder contratos por descumprir SLAs sem perceber que havia chamados críticos em aberto.

Este projeto foi desenvolvido como **Avaliação (AV)** da disciplina de **Paradigmas de Linguagens de Programação** do curso de Análise e Desenvolvimento de Sistemas — **CIESA**, Manaus/AM.

---

## 🗂️ Estrutura do Repositório

```
AV-Python-Ciesa-Solution/
├── helpdesk_levimoda_3.py   # Classes principais + cenário de demonstração
├── app.py                   # API REST com Flask
└── .gitignore
```

---

## ⚙️ Tecnologias

- **Python 3.x**
- **Flask** — API REST
- **datetime** — cálculo de SLA e tempo decorrido
- **collections.defaultdict** — relatórios e painel operacional

---

## 🏗️ Arquitetura — Orientação a Objetos

### `Chamado`

Representa um chamado de suporte aberto por um cliente.

| Atributo | Descrição |
|---|---|
| `numero` | Identificador único sequencial (gerado automaticamente) |
| `titulo` | Título resumido do problema |
| `descricao` | Descrição detalhada |
| `cliente` | Nome do cliente |
| `prioridade` | `baixa` / `media` / `alta` / `critica` |
| `status` | Estado atual do chamado |
| `data_abertura` | `datetime` do momento da criação |
| `sla_horas` | SLA calculado automaticamente pela prioridade |
| `tecnico` | ID do técnico responsável (ou `None`) |
| `historico` | Lista de ações registradas com data e responsável |

**Métodos principais:** `alterar_status()`, `esta_em_atraso()`, `tempo_decorrido()`, `registrar_acao()`, `to_dict()`

---

### `Tecnico`

Representa um técnico de suporte da equipe.

| Atributo | Descrição |
|---|---|
| `id_tecnico` | Identificador único sequencial |
| `nome` | Nome do técnico |
| `especialidades` | `set` de categorias de atuação |
| `chamados_ativos` | Lista dos números de chamados em andamento |
| `capacidade_maxima` | Limite de chamados simultâneos (padrão: 5) |
| `disponivel` | `True` se `len(chamados_ativos) < capacidade_maxima` |

**Métodos principais:** `atribuir_chamado()`, `liberar_chamado()`, `tem_especialidade()`, `to_dict()`

---

### `CentralDeSupporte`

Orquestra toda a operação: chamados, técnicos, fila e relatórios.

| Atributo | Descrição |
|---|---|
| `empresa` | Nome da empresa |
| `chamados` | **Dicionário** `{numero: Chamado}` — busca em **O(1)** |
| `tecnicos` | Dicionário `{id: Tecnico}` |
| `fila_nao_atribuidos` | Lista de números de chamados aguardando técnico |

**Métodos principais:** `abrir_chamado()`, `registrar_tecnico()`, `buscar_chamado()`, `atribuir_tecnico()`, `atribuicao_automatica()`, `resolver_chamado()`, `fechar_chamado()`, `listar_em_atraso()`, `relatorio_por_prioridade()`, `painel_operacional()`

> **Por que dicionário para `chamados`?**  
> O requisito crítico do cliente era localizar qualquer chamado pelo número em **tempo constante**, mesmo com milhares de registros. Um dicionário Python (`dict`) implementa uma **hash table**, garantindo acesso médio **O(1)** independentemente do volume de dados — ao contrário de listas, onde a busca seria O(n).

---

## 🔄 Fluxo de Status dos Chamados

```
aberto ──► em_atendimento ──► aguardando_cliente
                │                      │
                │◄──────────────────────┘
                │
                ▼
            resolvido ──► fechado
```

Qualquer tentativa de transição fora deste fluxo lança um `ValueError` com mensagem descritiva.

---

## ⏱️ SLA Automático

| Prioridade | SLA |
|---|---|
| 🔴 Crítica | 4 horas |
| 🟠 Alta | 8 horas |
| 🟡 Média | 24 horas |
| 🟢 Baixa | 72 horas |

O cálculo de atraso usa `datetime.timedelta`, comparando o tempo decorrido desde a abertura com o SLA definido. Chamados com status `resolvido` ou `fechado` nunca aparecem como atrasados.

---

## 🤖 Balanceamento de Carga Automático

O método `atribuicao_automatica()` percorre a fila de chamados não atribuídos e distribui cada um ao técnico disponível com **menos chamados ativos**. Em caso de empate, o técnico com **menor `id_tecnico`** é priorizado.

---

## 🚀 Como Executar

### Pré-requisitos

```bash
pip install flask
```

### Rodar a demonstração (modo terminal)

Executa o cenário de demonstração completo: criação de técnicos, abertura de chamados, atribuição automática, resolução, fechamento, simulação de atraso e painel operacional.

```bash
python helpdesk_levimoda_3.py
```

### Subir a API REST

```bash
python app.py
```

O servidor sobe em `http://localhost:5000` com `debug=True`.

---

## 🌐 Endpoints da API

Todas as rotas retornam **JSON**. Erros incluem o campo `"erro"` com mensagem descritiva e o código HTTP adequado.

### Chamados

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `POST` | `/chamados` | Abre um novo chamado | `201` |
| `GET` | `/chamados` | Lista todos (filtro opcional: `?status=`) | `200` |
| `GET` | `/chamados/<numero>` | Busca chamado pelo número | `200` / `404` |
| `PATCH` | `/chamados/<numero>/status` | Altera o status do chamado | `200` / `400` / `404` |
| `PATCH` | `/chamados/<numero>/resolver` | Resolve um chamado | `200` / `400` / `403` / `404` |
| `GET` | `/chamados/em-atraso` | Lista chamados fora do SLA, ordenados | `200` |

### Técnicos

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `POST` | `/tecnicos` | Registra novo técnico | `201` |
| `GET` | `/tecnicos` | Lista técnicos (filtro opcional: `?disponivel=true`) | `200` |

### Operações

| Método | Rota | Descrição | Status |
|---|---|---|---|
| `POST` | `/atribuicao/automatica` | Executa atribuição automática da fila | `200` |
| `GET` | `/painel` | Painel operacional completo | `200` |

---

### Exemplos de Request/Response

**Abrir chamado**
```http
POST /chamados
Content-Type: application/json

{
  "titulo": "Servidor fora do ar",
  "descricao": "Servidor de produção não responde desde as 08h.",
  "cliente": "Empresa A",
  "prioridade": "critica"
}
```

**Registrar técnico**
```http
POST /tecnicos
Content-Type: application/json

{
  "nome": "Alice",
  "especialidades": ["Redes", "Hardware"],
  "capacidade_maxima": 4
}
```

**Alterar status**
```http
PATCH /chamados/1/status
Content-Type: application/json

{
  "novo_status": "em_atendimento",
  "responsavel": "Alice"
}
```

**Resolver chamado**
```http
PATCH /chamados/1/resolver
Content-Type: application/json

{
  "id_tecnico": 1,
  "descricao_solucao": "Cabo de rede reconectado ao switch."
}
```

---

## 🧪 Cenário de Demonstração

Ao rodar `helpdesk_levimoda_3.py` diretamente, o script executa automaticamente:

1. Criação da central **"Ciesa Solutions"** com 4 técnicos de especialidades variadas
2. Abertura de 8 chamados com prioridades e clientes diferentes
3. Execução de `atribuicao_automatica()` com exibição dos resultados
4. Resolução de 2 chamados e fechamento de 1
5. Tentativa de transição de status inválida com tratamento de exceção
6. Simulação de chamado em atraso e exibição de `listar_em_atraso()`
7. Exibição do `painel_operacional()` completo em JSON

---

## 🏫 Informações Acadêmicas

| | |
|---|---|
| **Instituição** | Centro Universitário de Ensino Superior do Amazonas — CIESA |
| **Curso** | Análise e Desenvolvimento de Sistemas |
| **Disciplina** | Paradigmas de Linguagens de Programação |
| **Tipo** | Avaliação (AV) — Python com POO e API REST |

---

