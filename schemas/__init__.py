from schemas.aluno import (
    AlunoSchema,
    AlunoDeleteSchema,
    AlunoBuscaIdSchema,
    AlunoFiltroSchema,
    ListagemAlunosSchema,
    AlunoViewSchema,
    apresenta_aluno,
    apresenta_lista_alunos
)

from schemas.turma import (
    TurmaSchema,
    TurmaDeleteSchema,
    TurmaBuscaIdSchema,
    ListagemTurmaSchema,
    TurmaViewSchema,
    apresenta_turma,
    apresenta_lista_turmas
)

from schemas.error import ErrorSchema