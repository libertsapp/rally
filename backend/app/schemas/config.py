from pydantic import BaseModel, ConfigDict


class ConfigEntrada(BaseModel):
    estrelas_visiveis: bool = True
    checkin_data_aberta: str = ""
    checkin_travado: bool = False
    dias_para_rip: int = 60
    dias_para_aposentado: int = 100
    nome_grupo: str = ""
    subtitulo: str = ""
    logo_url: str = ""
    cor_primaria: str = ""
    cor_secundaria: str = ""
    link_rede_social: str = ""


class ConfigSaida(ConfigEntrada):
    model_config = ConfigDict(from_attributes=True)

    contador_acessos: int
