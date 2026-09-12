from pydantic import BaseModel


class RodadaDoPerfil(BaseModel):
    data: str
    time_nome: str
    is_winner: bool
    vitorias: int


class PontoAproveitamento(BaseModel):
    data: str
    pct: int


class ParceiroFrequente(BaseModel):
    id: str
    nome: str
    apelido: str = ""
    count: int


class PerfilSaida(BaseModel):
    jogos: int
    titulos: int
    vitorias_partidas: int
    vezes_na_foto: int
    pct: int
    rounds: list[RodadaDoPerfil]
    aproveitamento_series: list[PontoAproveitamento]
    parceiros: list[ParceiroFrequente]
