"""Espelha a aba "Config" do Apps Script legado: 1 linha de configurações por
organização (estrelasVisiveis, checkinDataAberta, checkinTravado,
contadorAcessos)."""

from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class Config(Base):
    __tablename__ = "config"

    organizacao_id = Column(String, primary_key=True, default="dev")
    estrelas_visiveis = Column(Boolean, default=True)
    checkin_data_aberta = Column(String, default="")  # "yyyy-mm-dd" ou "" (fechado)
    checkin_travado = Column(Boolean, default=False)
    contador_acessos = Column(Integer, default=0)
    dias_para_rip = Column(Integer, default=60)
    dias_para_aposentado = Column(Integer, default=100)

    # identidade visual do grupo — o que hoje é "dois HTMLs hardcoded" (Terça
    # navy/dourado, Meme roxo/neon) vira configuração por organização
    nome_grupo = Column(String, default="")
    subtitulo = Column(String, default="")
    logo_url = Column(String, default="")
    cor_primaria = Column(String, default="")
    cor_secundaria = Column(String, default="")
    link_rede_social = Column(String, default="")
