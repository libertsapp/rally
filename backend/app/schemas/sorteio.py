from pydantic import BaseModel

from app.schemas.jogador import JogadorSaida


class MontarGruposEntrada(BaseModel):
    jogador_ids: list[str]
    num_times: int


class SortearTimesEntrada(BaseModel):
    jogador_ids: list[str]
    num_times: int
    grupos: list[list[str]] | None = None  # ids por grupo, do modo híbrido "grupos + automático"
    considerar_historico: bool = True
    limite_rodadas_recentes: int = 5


TimeSorteado = list[JogadorSaida]
