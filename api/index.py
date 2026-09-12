"""Ponto de entrada único da Vercel: uma função Python que serve TANTO a API
quanto os arquivos estáticos do frontend.

Descobrimos na prática que, quando a Vercel detecta o projeto como um
"backend framework" (FastAPI), ela para de servir arquivos estáticos por
conta própria — todo caminho cai nessa função. Então a própria função
precisa decidir: /api/* vai pro FastAPI (backend/main.py), o resto vai pros
arquivos em frontend/ (com index.html como fallback de diretório).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app as fastapi_app  # noqa: E402

from starlette.applications import Starlette  # noqa: E402
from starlette.routing import Mount  # noqa: E402
from starlette.staticfiles import StaticFiles  # noqa: E402

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Starlette(
    routes=[
        Mount("/api", app=fastapi_app),
        Mount("/", app=StaticFiles(directory=FRONTEND_DIR, html=True)),
    ]
)
