from pydantic import BaseModel


class CampeaoSemana(BaseModel):
    data: str
    time_nome: str
    player_ids: list[str]


class ResumoDashboard(BaseModel):
    ano: str
    dias_jogados_no_ano: int
    jogadores_ativos: int
    desaparecidos: int
    campeao_semana: CampeaoSemana | None


class FotoLinha(BaseModel):
    id: str
    nome: str
    apelido: str = ""
    vezes: int


class DuplaLinha(BaseModel):
    id1: str
    id2: str
    count: int


class PanelaLinha(BaseModel):
    data: str
    time_nome: str
    player_ids: list[str]
    media_time: float
    media_outros: float
    diff: float


class AusenteLinha(BaseModel):
    id: str
    nome: str
    apelido: str = ""
    dias_sem_jogar: int
    status: str  # "rip" | "aposentado"
