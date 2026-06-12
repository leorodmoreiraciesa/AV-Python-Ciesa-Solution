from flask import Flask, request, jsonify
from helpdesk_levimoda_3 import (
    CentralDeSupporte, 
    ChamadoNaoEncontradoException, 
    CapacidadeExcedidaException
)

app = Flask(__name__)

# Instância Global da Central de Suporte para persistência em memória
central = CentralDeSupporte("Ciesa Solutions")

@app.route('/chamados', methods=['POST'])
def abrir_chamado():
    dados = request.get_json()
    try:
        chamado = central.abrir_chamado(
            titulo=dados['titulo'],
            descricao=dados['descricao'],
            cliente=dados['cliente'],
            prioridade=dados['prioridade']
        )
        return jsonify(chamado.to_dict()), 201
    except KeyError:
        return jsonify({"erro": "Campos obrigatorios: titulo, descricao, cliente, prioridade"}), 400
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/chamados', methods=['GET'])
def listar_chamados():
    status_filter = request.args.get('status')
    lista = []
    for chamado in central.chamados.values():
        if status_filter and chamado.status != status_filter.lower():
            continue
        lista.append(chamado.to_dict())
    return jsonify(lista), 200

@app.route('/chamados/<int:numero>', methods=['GET'])
def buscar_chamado(numero):
    try:
        chamado = central.buscar_chamado(numero)
        return jsonify(chamado.to_dict()), 200
    except ChamadoNaoEncontradoException as e:
        return jsonify({"erro": str(e)}), 404

@app.route('/chamados/<int:numero>/status', methods=['PATCH'])
def alterar_status(numero):
    dados = request.get_json()
    try:
        chamado = central.buscar_chamado(numero)
        chamado.alterar_status(dados['novo_status'], dados['responsavel'])
        return jsonify(chamado.to_dict()), 200
    except ChamadoNaoEncontradoException as e:
        return jsonify({"erro": str(e)}), 404
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except KeyError:
        return jsonify({"erro": "Campos obrigatorios: novo_status, responsavel"}), 400

@app.route('/chamados/<int:numero>/resolver', methods=['PATCH'])
def resolver_chamado(numero):
    dados = request.get_json()
    try:
        central.resolver_chamado(numero, dados['id_tecnico'], dados['descricao_solucao'])
        return jsonify({"mensagem": "Chamado resolvido com sucesso", "chamado": central.buscar_chamado(numero).to_dict()}), 200
    except ChamadoNaoEncontradoException as e:
        return jsonify({"erro": str(e)}), 404
    except PermissionError as e:
        return jsonify({"erro": str(e)}), 403
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except KeyError:
        return jsonify({"erro": "Campos obrigatorios: id_tecnico, descricao_solucao"}), 400

@app.route('/chamados/em-atraso', methods=['GET'])
def listar_em_atraso():
    atrasados = central.listar_em_atraso()
    return jsonify([c.to_dict() for c in atrasados]), 200

@app.route('/tecnicos', methods=['POST'])
def registrar_tecnico():
    dados = request.get_json()
    try:
        cap_max = dados.get('capacidade_maxima', 5)
        tecnico = central.registrar_tecnico(
            nome=dados['nome'],
            especialidades=dados['especialidades'],
            capacidade_maxima=cap_max
        )
        return jsonify(tecnico.to_dict()), 201
    except KeyError:
        return jsonify({"erro": "Campos obrigatorios: nome, especialidades"}), 400

@app.route('/tecnicos', methods=['GET'])
def listar_tecnicos():
    disp_filter = request.args.get('disponivel')
    lista = []
    for tecnico in central.tecnicos.values():
        if disp_filter is not None:
            filtro_bool = disp_filter.lower() == 'true'
            if tecnico.disponivel != filtro_bool:
                continue
        lista.append(tecnico.to_dict())
    return jsonify(lista), 200

@app.route('/atribuicao/automatica', methods=['POST'])
def exec_atribuicao_automatica():
    qnt, atribuidos = central.atribuicao_automatica()
    return jsonify({
        "quantidade_atribuida": qnt,
        "chamados_atribuidos": atribuidos
    }), 200

@app.route('/painel', methods=['GET'])
def obter_painel():
    return jsonify(central.painel_operacional()), 200

if __name__ == '__main__':
    # Rodando o servidor
    app.run(debug=True, port=5000)

