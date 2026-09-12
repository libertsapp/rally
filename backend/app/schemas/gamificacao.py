from pydantic import BaseModel


class Badges(BaseModel):
    top1: list[str]
    paneleiro: list[str]
    mochila: list[str]
    grudento: list[str]
    rip: list[str]
    aposentado: list[str]
    cabeca_de_chave: list[str]


class HallVencedor(BaseModel):
    id: str
    nome: str
    apelido: str = ""
    count: int


class HallPeriodo(BaseModel):
    periodo: str
    vencedores: list[HallVencedor]
