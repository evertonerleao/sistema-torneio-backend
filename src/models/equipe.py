from src.models.user import db
import uuid

class Equipe(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Equipe {self.nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome
        }

class Partida(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    equipe1_id = db.Column(db.String(36), db.ForeignKey('equipe.id'), nullable=True)
    equipe2_id = db.Column(db.String(36), db.ForeignKey('equipe.id'), nullable=True)
    vencedor_id = db.Column(db.String(36), db.ForeignKey('equipe.id'), nullable=True)
    rodada = db.Column(db.Integer, nullable=False)
    posicao = db.Column(db.Integer, nullable=False)  # posição na rodada
    
    # Relacionamentos
    equipe1 = db.relationship('Equipe', foreign_keys=[equipe1_id], backref='partidas_como_equipe1')
    equipe2 = db.relationship('Equipe', foreign_keys=[equipe2_id], backref='partidas_como_equipe2')
    vencedor = db.relationship('Equipe', foreign_keys=[vencedor_id], backref='partidas_vencidas')
    
    def __repr__(self):
        return f'<Partida {self.equipe1.nome if self.equipe1 else "TBD"} vs {self.equipe2.nome if self.equipe2 else "TBD"}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'equipe1': self.equipe1.to_dict() if self.equipe1 else None,
            'equipe2': self.equipe2.to_dict() if self.equipe2 else None,
            'vencedor': self.vencedor.to_dict() if self.vencedor else None,
            'rodada': self.rodada,
            'posicao': self.posicao
        }

class Torneio(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='criado')  # criado, em_andamento, finalizado
    
    def __repr__(self):
        return f'<Torneio {self.nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'status': self.status
        }

