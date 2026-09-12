from pydantic import BaseModel, ConfigDict


class ConvidarAdminEntrada(BaseModel):
    email: str


class UsuarioSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    tipo: str
    organizacao_id: str | None
    ativo: bool
