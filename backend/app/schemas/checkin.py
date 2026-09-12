from pydantic import BaseModel, ConfigDict


class CheckinEntrada(BaseModel):
    jogador_id: str
    jogador_nome: str = ""
    estrelas: float = 0
    sexo: str = ""


class CheckinSaida(CheckinEntrada):
    model_config = ConfigDict(from_attributes=True)

    id: str
    data: str
