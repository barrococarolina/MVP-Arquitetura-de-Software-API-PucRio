from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from model.base import Base
import os
from model.turma import Turma
from model.aluno import Aluno

# Define o caminho do diretório onde o banco de dados será armazenado
db_path = "database/"
if not os.path.exists(db_path):
    os.makedirs(db_path)

db_url = f"sqlite:///{db_path}/db.sqlite3"
engine = create_engine(db_url, echo=False)

# Verifica se o banco de dados não existe
if not database_exists(engine.url):
    create_database(engine.url)

# Cria as tabelas do banco, caso não existam
Base.metadata.create_all(engine)

# Cria a sessão
Session = sessionmaker(bind=engine)