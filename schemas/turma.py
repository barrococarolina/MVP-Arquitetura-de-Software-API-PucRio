from typing import List
from pydantic import BaseModel, Field
from model.turma import Turma

class TurmaSchema(BaseModel):
    nome: str = Field(min_length=2, max_length=140, examples=["Matemática"])
    ativo: bool = True


class TurmaViewSchema(BaseModel):
    id: int
    nome: str
    ativo: bool


class ListagemTurmaSchema(BaseModel):
    turmas: List[TurmaViewSchema]


class TurmaBuscaIdSchema(BaseModel):
    id: int = Field(gt=0, examples=[1])


class TurmaDeleteSchema(BaseModel):
    message: str
    id: int


def apresenta_turma(turma: Turma) -> dict:
    return {"id": turma.id, "nome": turma.nome, "ativo": turma.ativo}


def apresenta_lista_turmas(lista_turmas: list[Turma]) -> dict:
    return {"turmas": [apresenta_turma(turma) for turma in lista_turmas]}
