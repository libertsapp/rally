from pydantic import BaseModel, ConfigDict


class RodadaTimeEntrada(BaseModel):
    nome: str = ""
    player_ids: list[str] = []
    vitorias: int = 0


class RodadaEntrada(BaseModel):
    data: str  # "yyyy-mm-dd"
    rascunho: bool = False
    vencedor: int = -1  # índice do time campeão em `times`, -1 se nenhum
    times: list[RodadaTimeEntrada]


class RodadaTimeSaida(RodadaTimeEntrada):
    model_config = ConfigDict(from_attributes=True)


class RodadaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    data: str
    rascunho: bool
    vencedor: int
    times: list[RodadaTimeSaida]
