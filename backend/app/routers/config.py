from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import Config
from app.schemas.config import ConfigEntrada, ConfigSaida

router = APIRouter(prefix="/config", tags=["config"])

ORGANIZACAO_PADRAO = "dev"


def get_or_create_config(db: Session) -> Config:
    config = db.query(Config).filter(Config.organizacao_id == ORGANIZACAO_PADRAO).first()
    if not config:
        config = Config(organizacao_id=ORGANIZACAO_PADRAO)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ConfigSaida)
def obter_config(db: Session = Depends(get_db)):
    return get_or_create_config(db)


@router.put("", response_model=ConfigSaida)
def atualizar_config(dados: ConfigEntrada, db: Session = Depends(get_db)):
    # o contador de acessos nunca é aceito por aqui — só /config/acesso mexe nele,
    # senão uma gravação de configuração desatualizada (aberta antes de outros
    # acessos) sobrescreveria o contador com um valor velho
    config = get_or_create_config(db)
    config.estrelas_visiveis = dados.estrelas_visiveis
    config.checkin_data_aberta = dados.checkin_data_aberta
    config.checkin_travado = dados.checkin_travado
    config.dias_para_rip = dados.dias_para_rip
    config.dias_para_aposentado = dados.dias_para_aposentado
    config.nome_grupo = dados.nome_grupo
    config.subtitulo = dados.subtitulo
    config.logo_url = dados.logo_url
    config.cor_primaria = dados.cor_primaria
    config.cor_secundaria = dados.cor_secundaria
    config.link_rede_social = dados.link_rede_social
    db.commit()
    db.refresh(config)
    return config


@router.post("/acesso", response_model=ConfigSaida)
def registrar_acesso(db: Session = Depends(get_db)):
    config = get_or_create_config(db)
    config.contador_acessos = (config.contador_acessos or 0) + 1
    db.commit()
    db.refresh(config)
    return config
