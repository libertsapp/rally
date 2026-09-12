from pydantic import BaseModel


class RankingLinha(BaseModel):
    id: str
    nome: str
    apelido: str = ""
    jogos: int
    titulos: int
    vitorias_partidas: int
    pct: int
    datas_campeao: list[str]
