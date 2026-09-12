from pydantic import BaseModel, ConfigDict


class OrganizacaoEntrada(BaseModel):
    slug: str
    nome: str
    subtitulo: str = ""
    logo_url: str = ""
    cor_primaria: str = ""
    cor_secundaria: str = ""
    link_rede_social: str = ""
    plano: str = "gratuito"


class OrganizacaoAtualizar(BaseModel):
    nome: str
    subtitulo: str = ""
    logo_url: str = ""
    cor_primaria: str = ""
    cor_secundaria: str = ""
    link_rede_social: str = ""
    plano: str = "gratuito"


class OrganizacaoSaida(OrganizacaoEntrada):
    model_config = ConfigDict(from_attributes=True)

    id: str
