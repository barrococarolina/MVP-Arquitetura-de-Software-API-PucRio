from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from model.base import Base

class Aluno(Base):
    __tablename__ = "aluno"

    id = Column("pk_aluno", Integer, primary_key=True)
    nome = Column(String(140), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    faltas = Column(Integer, nullable=False, default=0)
    turmaId = Column(Integer, ForeignKey("turma.pk_turma"), nullable=False)

    cep = Column(String(8), nullable=True)
    logradouro = Column(String(255), nullable=True)
    bairro = Column(String(255), nullable=True)
    cidade = Column(String(255), nullable=True)
    uf = Column(String(2), nullable=True)

    turma = relationship("Turma", back_populates="alunos")

    def __init__(
        self,
        nome: str,
        email: str,
        faltas: int,
        turmaId: int,
        cep: str | None = None,
        logradouro: str | None = None,
        bairro: str | None = None,
        cidade: str | None = None,
        uf: str | None = None,
    ):
        self.nome = nome.strip()
        self.email = email.strip()
        self.faltas = faltas
        self.turmaId = turmaId
        self.cep = cep
        self.logradouro = logradouro
        self.bairro = bairro
        self.cidade = cidade
        self.uf = uf
