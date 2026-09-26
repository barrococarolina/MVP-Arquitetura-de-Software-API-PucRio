import re

import requests
from flask import redirect
from flask_cors import CORS
from flask_openapi3 import Info, OpenAPI, Tag
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from logger import logger
from model.aluno import Aluno
from model.session import Session
from model.turma import Turma
from schemas.aluno import (
    AlunoBuscaIdSchema,
    AlunoDeleteSchema,
    AlunoFiltroSchema,
    AlunoSchema,
    AlunoViewSchema,
    ListagemAlunosSchema,
    apresenta_aluno,
    apresenta_lista_alunos,
)
from schemas.error import ErrorSchema
from schemas.turma import (
    ListagemTurmaSchema,
    TurmaBuscaIdSchema,
    TurmaDeleteSchema,
    TurmaSchema,
    TurmaViewSchema,
    apresenta_lista_turmas,
    apresenta_turma,
)


info = Info(
    title="Sistema de Gerenciamento Escolar - API",
    version="2.0.0",
    description=(
        "API REST para gerenciamento de alunos e turmas, com persistência em "
        "SQLite e integração com a API pública ViaCEP."
    ),
)
app = OpenAPI(__name__, info=info)
CORS(app, resources={r"/*": {"origins": "*"}})

home_tag = Tag(name="Documentação", description="Documentação da API")
aluno_tag = Tag(name="Aluno", description="Cadastro, consulta, edição e remoção de alunos")
turma_tag = Tag(name="Turma", description="Cadastro, consulta, edição e remoção de turmas")

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"


def normalizar_cep(cep: str | None) -> str | None:
    if not cep:
        return None
    somente_digitos = re.sub(r"\D", "", cep)
    if len(somente_digitos) != 8:
        raise ValueError("O CEP deve conter 8 dígitos.")
    return somente_digitos


def consultar_viacep(cep: str | None) -> dict:
    """Consulta e trata o endereço retornado pelo ViaCEP."""
    cep_normalizado = normalizar_cep(cep)
    if not cep_normalizado:
        return {}

    try:
        response = requests.get(VIACEP_URL.format(cep=cep_normalizado), timeout=5)
        response.raise_for_status()
        dados = response.json()
    except requests.RequestException as exc:
        logger.error("Erro ao consultar ViaCEP: %s", exc)
        raise RuntimeError("Não foi possível consultar o serviço ViaCEP.") from exc

    if dados.get("erro"):
        raise ValueError("CEP não encontrado no ViaCEP.")

    return {
        "cep": dados.get("cep", cep_normalizado).replace("-", ""),
        "logradouro": dados.get("logradouro"),
        "bairro": dados.get("bairro"),
        "cidade": dados.get("localidade"),
        "uf": dados.get("uf"),
    }


def validar_turma(session, turma_id: int):
    turma = session.query(Turma).filter(Turma.id == turma_id).first()
    if not turma:
        raise ValueError(f"Turma com id {turma_id} não encontrada.")
    return turma


@app.get("/", tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect("/openapi")


@app.post("/aluno", tags=[aluno_tag], responses={"200": AlunoViewSchema, "400": ErrorSchema, "409": ErrorSchema})
def add_aluno(body: AlunoSchema):
    """Adiciona um novo Aluno à base de dados.

    Só permite o cadastro se a turma informada existir.

    Retorna uma representação dos alunos e turmas associados.
    """
    session = Session()
    try:
        validar_turma(session, body.turmaId)
        endereco = consultar_viacep(body.cep)
        aluno = Aluno(
            nome=body.nome,
            email=body.email,
            faltas=body.faltas,
            turmaId=body.turmaId,
            **endereco,
        )
        session.add(aluno)
        session.commit()
        return apresenta_aluno(aluno), 200
    except ValueError as exc:
        session.rollback()
        return {"message": str(exc)}, 400
    except RuntimeError as exc:
        session.rollback()
        return {"message": str(exc)}, 502
    except IntegrityError:
        session.rollback()
        return {"message": "Já existe um aluno com esse nome."}, 409
    except Exception as exc:
        session.rollback()
        logger.exception("Erro ao cadastrar aluno: %s", exc)
        return {"message": "Não foi possível salvar o aluno."}, 400
    finally:
        session.close()


@app.get("/aluno", tags=[aluno_tag], responses={"200": ListagemAlunosSchema})
def get_alunos(query: AlunoFiltroSchema):
    """Faz a busca por todos os alunos cadastrados e permite busca por nome/email e filtro por turma.
    """
    # O endpoint mantém compatibilidade com GET /aluno sem parâmetros.
    session = Session()
    try:
        busca_nome = (query.buscaNome or "").strip()
        turma_id = query.turmaId
        ordenacao = query.ordenar

        consulta = session.query(Aluno)
        if busca_nome:
            termo = f"%{busca_nome}%"
            consulta = consulta.filter(or_(Aluno.nome.ilike(termo), Aluno.email.ilike(termo)))
        if turma_id:
            consulta = consulta.filter(Aluno.turmaId == turma_id)

        if ordenacao == "faltas_desc":
            consulta = consulta.order_by(Aluno.faltas.desc())
        else:
            consulta = consulta.order_by(Aluno.nome.asc())

        return apresenta_lista_alunos(consulta.all()), 200
    finally:
        session.close()


@app.get("/aluno/<int:id>", tags=[aluno_tag], responses={"200": AlunoViewSchema, "404": ErrorSchema})
def get_aluno_id(path: AlunoBuscaIdSchema):
    """Faz a busca por um Aluno a partir do id do aluno.

    Retorna uma representação do aluno selecionado.
    """
    session = Session()
    try:
        aluno = session.query(Aluno).filter(Aluno.id == path.id).first()
        if not aluno:
            return {"message": "Aluno não encontrado."}, 404
        return apresenta_aluno(aluno), 200
    finally:
        session.close()


@app.put("/aluno/<int:id>", tags=[aluno_tag], responses={"200": AlunoViewSchema, "400": ErrorSchema, "404": ErrorSchema, "409": ErrorSchema})
def update_aluno(path: AlunoBuscaIdSchema, body: AlunoSchema):
    """Atualiza os dados de um Aluno
    """
    session = Session()
    try:
        aluno = session.query(Aluno).filter(Aluno.id == path.id).first()
        if not aluno:
            return {"message": "Aluno não encontrado."}, 404

        validar_turma(session, body.turmaId)
        endereco = consultar_viacep(body.cep)

        aluno.nome = body.nome.strip()
        aluno.email = body.email.strip()
        aluno.faltas = body.faltas
        aluno.turmaId = body.turmaId
        aluno.cep = endereco.get("cep") if endereco else None
        aluno.logradouro = endereco.get("logradouro") if endereco else None
        aluno.bairro = endereco.get("bairro") if endereco else None
        aluno.cidade = endereco.get("cidade") if endereco else None
        aluno.uf = endereco.get("uf") if endereco else None

        session.commit()
        return apresenta_aluno(aluno), 200
    except ValueError as exc:
        session.rollback()
        return {"message": str(exc)}, 400
    except RuntimeError as exc:
        session.rollback()
        return {"message": str(exc)}, 502
    except IntegrityError:
        session.rollback()
        return {"message": "Já existe outro aluno com esse nome."}, 409
    finally:
        session.close()


@app.delete("/aluno/<int:id>", tags=[aluno_tag], responses={"200": AlunoDeleteSchema, "404": ErrorSchema})
def del_aluno(path: AlunoBuscaIdSchema):
    """Deleta um aluno a partir do id de aluno informado

    Retorna uma mensagem de confirmação da remoção.
    """
    session = Session()
    try:
        aluno = session.query(Aluno).filter(Aluno.id == path.id).first()
        if not aluno:
            return {"message": "Aluno não encontrado."}, 404
        nome = aluno.nome
        session.delete(aluno)
        session.commit()
        return {"message": f"Aluno '{nome}' removido.", "id": path.id}, 200
    finally:
        session.close()


@app.post("/turma", tags=[turma_tag], responses={"200": TurmaViewSchema, "400": ErrorSchema, "409": ErrorSchema})
def add_turma(body: TurmaSchema):
    """Adiciona uma nova turma à base de dados

    Retorna uma representação das turmas.
    """
    session = Session()
    try:
        turma = Turma(nome=body.nome, ativo=body.ativo)
        session.add(turma)
        session.commit()
        return apresenta_turma(turma), 200
    except IntegrityError:
        session.rollback()
        return {"message": "Já existe uma turma com esse nome."}, 409
    except Exception as exc:
        session.rollback()
        logger.exception("Erro ao cadastrar turma: %s", exc)
        return {"message": "Não foi possível salvar a turma."}, 400
    finally:
        session.close()


@app.get("/turma", tags=[turma_tag], responses={"200": ListagemTurmaSchema})
def get_turmas():
    """Faz a busca por todas as turmas cadastradas

    Retorna uma representação da listagem de turmas.
    """
    session = Session()
    try:
        turmas = session.query(Turma).order_by(Turma.nome.asc()).all()
        return apresenta_lista_turmas(turmas), 200
    finally:
        session.close()


@app.get("/turma/<int:id>", tags=[turma_tag], responses={"200": TurmaViewSchema, "404": ErrorSchema})
def get_turma_id(path: TurmaBuscaIdSchema):
    """Faz a busca por uma turma a partir do id da turma.
    """
    session = Session()
    try:
        turma = session.query(Turma).filter(Turma.id == path.id).first()
        if not turma:
            return {"message": "Turma não encontrada."}, 404
        return apresenta_turma(turma), 200
    finally:
        session.close()


@app.put("/turma/<int:id>", tags=[turma_tag], responses={"200": TurmaViewSchema, "404": ErrorSchema, "409": ErrorSchema})
def update_turma(path: TurmaBuscaIdSchema, body: TurmaSchema):
    """Atualiza os dados de uma turma
    """
    session = Session()
    try:
        turma = session.query(Turma).filter(Turma.id == path.id).first()
        if not turma:
            return {"message": "Turma não encontrada."}, 404
        turma.nome = body.nome.strip()
        turma.ativo = body.ativo
        session.commit()
        return apresenta_turma(turma), 200
    except IntegrityError:
        session.rollback()
        return {"message": "Já existe outra turma com esse nome."}, 409
    finally:
        session.close()


@app.delete("/turma/<int:id>", tags=[turma_tag], responses={"200": TurmaDeleteSchema, "400": ErrorSchema, "404": ErrorSchema})
def del_turma(path: TurmaBuscaIdSchema):
    """Deleta uma turma a partir do id de turma informado

    Só permite a deleção se não houver alunos cadastrados na turma.

    Retorna uma mensagem de confirmação da remoção se tudo correr certo.
    """
    session = Session()
    try:
        turma = session.query(Turma).filter(Turma.id == path.id).first()
        if not turma:
            return {"message": "Turma não encontrada."}, 404
        if session.query(Aluno).filter(Aluno.turmaId == path.id).count() > 0:
            return {"message": "Não é possível excluir a turma porque existem alunos vinculados."}, 400
        session.delete(turma)
        session.commit()
        return {"message": "Turma excluída com sucesso.", "id": path.id}, 200
    finally:
        session.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
