"""Extensões compartilhadas da aplicação (sem importar `app`).

Mantém `db` fora de `app.py` para que `models/db_models.py` possa importar
a instância SQLAlchemy sem dependência circular com o módulo da aplicação.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
