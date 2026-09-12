"""Espelha a aba "Config" do Apps Script legado: 1 linha de configurações
OPERACIONAIS por organização (estrelasVisiveis, checkinDataAberta,
checkinTravado, contadorAcessos). A identidade visual (nome, cores, logo)
mora em Organizacao — Config é só o "estado do dia a dia"."""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.database import Base


class Config(Base):
    __tablename__ = "config"

    organizacao_id = Column(String, ForeignKey("organizacoes.id"), primary_key=True)
    estrelas_visiveis = Column(Boolean, default=True)
    checkin_data_aberta = Column(String, default="")  # "yyyy-mm-dd" ou "" (fechado)
    checkin_travado = Column(Boolean, default=False)
    contador_acessos = Column(Integer, default=0)
    dias_para_rip = Column(Integer, default=60)
    dias_para_aposentado = Column(Integer, default=100)
