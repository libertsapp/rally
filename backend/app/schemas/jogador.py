from typing import Optional

from pydantic import BaseModel, ConfigDict


class JogadorEntrada(BaseModel):
    nome: str
    apelido: Optional[str] = ""
    foto: Optional[str] = ""
    estrelas: Optional[float] = 0
    sexo: Optional[str] = ""
    porte: Optional[str] = ""


class JogadorSaida(JogadorEntrada):
    model_config = ConfigDict(from_attributes=True)

    id: str
