from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.config import Config
from app.models.organizacao import Organizacao
from app.schemas.config import ConfigEntrada, ConfigSaida
from app.tenant import get_organizacao_atual

router = APIRouter(prefix="/config", tags=["config"])


def get_or_create_config(db: Session, organizacao_id: str) -> Config:
    config = db.query(Config).filter(Config.organizacao_id == organizacao_id).first()
    if not config:
        config = Config(organizacao_id=organizacao_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ConfigSaida)
def obter_config(db: Session = Depends(get_db), organizacao: Organizacao = Depends(get_organizacao_atual)):
    return get_or_create_config(db, organizacao.id)


@router.put("", response_model=ConfigSaida)
def atualizar_config(
    dados: ConfigEntrada,
    db: Session = Depends(get_db),
    organizacao: Organizacao = Depends(get_organizacao_atual),
):
    # o contador de acessos nunca é aceito por aqui — só /config/acesso mexe nele,
    # senão uma gravação de configuração desatualizada (aberta antes de outros
    # acessos) sobrescreveria o contador com um valor velho
    config = get_or_create_config(db, organizacao.id)
    config.estrelas_visiveis = dados.estrelas_visiveis
    config.checkin_data_aberta = dados.checkin_data_aberta
    config.checkin_travado = dados.checkin_travado
    config.dias_para_rip = dados.dias_para_rip
    config.dias_para_aposentado = dados.dias_para_aposentado
    db.commit()
    db.refresh(config)
    return config


@router.post("/acesso", response_model=ConfigSaida)
def registrar_acesso(db: Session = Depends(get_db), organizacao: Organizacao = Depends(get_organizacao_atual)):
    config = get_or_create_config(db, organizacao.id)
    config.contador_acessos = (config.contador_acessos or 0) + 1
    db.commit()
    db.refresh(config)
    return config
