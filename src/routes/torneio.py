from flask import Blueprint, jsonify, request
from src.models.equipe import Equipe, Partida, Torneio, db
import random
import math

torneio_bp = Blueprint('torneio', __name__)

@torneio_bp.route('/equipes', methods=['GET'])
def get_equipes():
    equipes = Equipe.query.all()
    return jsonify([equipe.to_dict() for equipe in equipes])

@torneio_bp.route('/equipes', methods=['POST'])
def create_equipe():
    data = request.json
    
    # Verificar se a equipe já existe
    equipe_existente = Equipe.query.filter_by(nome=data['nome']).first()
    if equipe_existente:
        return jsonify({'erro': 'Equipe já existe'}), 400
    
    equipe = Equipe(nome=data['nome'])
    db.session.add(equipe)
    db.session.commit()
    return jsonify(equipe.to_dict()), 201

@torneio_bp.route('/equipes/<string:equipe_id>', methods=['DELETE'])
def delete_equipe(equipe_id):
    equipe = Equipe.query.get_or_404(equipe_id)
    db.session.delete(equipe)
    db.session.commit()
    return '', 204

@torneio_bp.route('/equipes/limpar', methods=['DELETE'])
def limpar_equipes():
    # Limpar todas as partidas primeiro (devido às foreign keys)
    Partida.query.delete()
    Equipe.query.delete()
    db.session.commit()
    return jsonify({'mensagem': 'Todas as equipes foram removidas'}), 200

@torneio_bp.route('/sorteio', methods=['POST'])
def realizar_sorteio():
    equipes = Equipe.query.all()
    
    if len(equipes) < 2:
        return jsonify({'erro': 'É necessário pelo menos 2 equipes para realizar o sorteio'}), 400
    
    # Embaralhar as equipes
    equipes_sorteadas = list(equipes)
    random.shuffle(equipes_sorteadas)
    
    return jsonify([equipe.to_dict() for equipe in equipes_sorteadas])

@torneio_bp.route('/chaveamento', methods=['POST'])
def gerar_chaveamento():
    data = request.json
    equipes_ids = data.get('equipes_ids', [])
    
    if len(equipes_ids) < 2:
        return jsonify({'erro': 'É necessário pelo menos 2 equipes para gerar o chaveamento'}), 400
    
    # Limpar partidas existentes
    Partida.query.delete()
    db.session.commit()
    
    # Calcular o número de equipes para a próxima potência de 2
    num_equipes = len(equipes_ids)
    proxima_potencia_2 = 2 ** math.ceil(math.log2(num_equipes))
    
    # Criar a primeira rodada
    rodada = 1
    posicao = 1
    partidas_criadas = []
    
    # Se o número de equipes não é uma potência de 2, algumas equipes passam direto
    equipes_restantes = equipes_ids.copy()
    
    # Criar partidas da primeira rodada
    while len(equipes_restantes) >= 2:
        equipe1_id = equipes_restantes.pop(0)
        equipe2_id = equipes_restantes.pop(0)
        
        partida = Partida(
            equipe1_id=equipe1_id,
            equipe2_id=equipe2_id,
            rodada=rodada,
            posicao=posicao
        )
        db.session.add(partida)
        partidas_criadas.append(partida)
        posicao += 1
    
    # Se sobrou uma equipe, ela passa direto para a próxima rodada
    if equipes_restantes:
        partida = Partida(
            equipe1_id=equipes_restantes[0],
            equipe2_id=None,  # BYE
            rodada=rodada,
            posicao=posicao
        )
        db.session.add(partida)
        partidas_criadas.append(partida)
    
    # Criar as rodadas subsequentes (vazias, serão preenchidas conforme o torneio avança)
    num_rodadas = math.ceil(math.log2(num_equipes))
    for r in range(2, num_rodadas + 1):
        num_partidas_rodada = max(1, proxima_potencia_2 // (2 ** r))
        for p in range(1, num_partidas_rodada + 1):
            partida = Partida(
                equipe1_id=None,
                equipe2_id=None,
                rodada=r,
                posicao=p
            )
            db.session.add(partida)
            partidas_criadas.append(partida)
    
    db.session.commit()
    
    # Retornar todas as partidas organizadas por rodada
    partidas = Partida.query.order_by(Partida.rodada, Partida.posicao).all()
    chaveamento = {}
    
    for partida in partidas:
        rodada_str = f'rodada_{partida.rodada}'
        if rodada_str not in chaveamento:
            chaveamento[rodada_str] = []
        chaveamento[rodada_str].append(partida.to_dict())
    
    return jsonify(chaveamento)

@torneio_bp.route('/partidas', methods=['GET'])
def get_partidas():
    partidas = Partida.query.order_by(Partida.rodada, Partida.posicao).all()
    chaveamento = {}
    
    for partida in partidas:
        rodada_str = f'rodada_{partida.rodada}'
        if rodada_str not in chaveamento:
            chaveamento[rodada_str] = []
        chaveamento[rodada_str].append(partida.to_dict())
    
    return jsonify(chaveamento)

@torneio_bp.route('/partidas/<string:partida_id>/vencedor', methods=['PUT'])
def definir_vencedor(partida_id):
    data = request.json
    vencedor_id = data.get('vencedor_id')
    
    partida = Partida.query.get_or_404(partida_id)
    
    # Verificar se o vencedor é uma das equipes da partida
    if vencedor_id not in [partida.equipe1_id, partida.equipe2_id]:
        return jsonify({'erro': 'Vencedor deve ser uma das equipes da partida'}), 400
    
    partida.vencedor_id = vencedor_id
    
    # Avançar o vencedor para a próxima rodada
    proxima_rodada = partida.rodada + 1
    proxima_posicao = (partida.posicao + 1) // 2  # Calcular posição na próxima rodada
    
    proxima_partida = Partida.query.filter_by(
        rodada=proxima_rodada,
        posicao=proxima_posicao
    ).first()
    
    if proxima_partida:
        # Determinar se o vencedor vai para equipe1 ou equipe2 da próxima partida
        if partida.posicao % 2 == 1:  # Posição ímpar vai para equipe1
            proxima_partida.equipe1_id = vencedor_id
        else:  # Posição par vai para equipe2
            proxima_partida.equipe2_id = vencedor_id
    
    db.session.commit()
    
    return jsonify(partida.to_dict())

