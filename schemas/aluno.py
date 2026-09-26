from typing import List
from pydantic import BaseModel, Field
from model.aluno import Aluno

class AlunoSchema(BaseModel):
    nome: str = Field(min_length=2, max_length=140, examples=["Maria Silva"])
    email: str = Field(min_length=5, max_length=255, examples=["maria@email.com"])
    faltas: int = Field(default=0, ge=0, examples=[2])
    turmaId: int = Field(gt=0, examples=[1])
    cep: str | None = Field(default=None, examples=["22790000"], coerce_numbers_to_str=True)


class AlunoFiltroSchema(BaseModel):
    buscaNome: str | None = None
    turmaId: int | None = Field(default=None, gt=0)
    ordenar: str = "nome"


class AlunoBuscaIdSchema(BaseModel):
    id: int = Field(gt=0, examples={"example": {"value": 1}})


class AlunoViewSchema(BaseModel):
    id: int
    nome: str
    email: str
    faltas: int
    turmaId: int
    cep: str | None = None
    logradouro: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None


class ListagemAlunosSchema(BaseModel):
    alunos: List[AlunoViewSchema]


class AlunoDeleteSchema(BaseModel):
    message: str
    id: int


def apresenta_aluno(aluno: Aluno) -> dict:
    return {
        "id": aluno.id,
        "nome": aluno.nome,
        "email": aluno.email,
        "faltas": aluno.faltas,
        "turmaId": aluno.turmaId,
        "cep": aluno.cep,
        "logradouro": aluno.logradouro,
        "bairro": aluno.bairro,
        "cidade": aluno.cidade,
        "uf": aluno.uf,
    }


def apresenta_lista_alunos(lista_alunos: list[Aluno]) -> dict:
    return {"alunos": [apresenta_aluno(aluno) for aluno in lista_alunos]}
