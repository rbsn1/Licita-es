import datetime
import enum
import secrets

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data.db import Base


class Esfera(str, enum.Enum):
    federal = "federal"
    estadual = "estadual"
    municipal = "municipal"


class CanalAlerta(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"


class StatusAlerta(str, enum.Enum):
    pendente = "pendente"
    enviado = "enviado"
    falhou = "falhou"


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    razao_social: Mapped[str] = mapped_column(String(255))
    cnpj: Mapped[str] = mapped_column(String(14), unique=True)
    email: Mapped[str] = mapped_column(String(255))
    access_token: Mapped[str] = mapped_column(
        String(64), unique=True, default=lambda: secrets.token_urlsafe(32)
    )
    senha_hash: Mapped[str | None] = mapped_column(String(60), nullable=True)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    perfil: Mapped["PerfilCliente"] = relationship(back_populates="cliente", uselist=False)


# RF-AUTH-02: operador da consultoria — login do painel administrativo
class Operador(Base):
    __tablename__ = "operadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(60))
    criado_em: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class PerfilCliente(Base):
    __tablename__ = "perfis_cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), unique=True)
    cnaes: Mapped[list[str]] = mapped_column(ARRAY(String))
    ufs: Mapped[list[str]] = mapped_column(ARRAY(String))
    palavras_chave: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    valor_minimo: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    valor_maximo: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="perfil")


class Edital(Base):
    __tablename__ = "editais"

    id: Mapped[int] = mapped_column(primary_key=True)
    pncp_id: Mapped[str] = mapped_column(String(64), unique=True)
    orgao: Mapped[str] = mapped_column(String(255))
    objeto: Mapped[str] = mapped_column(String)
    esfera: Mapped[Esfera]
    modalidade: Mapped[str] = mapped_column(String(64))
    uf: Mapped[str] = mapped_column(String(2))
    municipio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    valor_estimado: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    data_publicacao: Mapped[datetime.date]
    link_pncp: Mapped[str] = mapped_column(String)


# RF-ANL-01/RF-ANL-02: resumo estruturado do edital, um por Edital (não por
# cliente — o conteúdo do edital independe de quem deu match nele; reaproveitado
# entre clientes que dão match no mesmo edital)
class ResumoEdital(Base):
    __tablename__ = "resumos_edital"

    id: Mapped[int] = mapped_column(primary_key=True)
    edital_id: Mapped[int] = mapped_column(ForeignKey("editais.id"), unique=True)
    prazo_limite_proposta: Mapped[datetime.datetime | None] = mapped_column(nullable=True)
    valor_estimado: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    requisitos_habilitacao: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    clausulas_risco: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    edital: Mapped["Edital"] = relationship()


# RF-PRE-01/RF-PRE-02: faixa de preço sugerida, um por Edital (mesma lógica do
# ResumoEdital — o cálculo não depende do cliente que deu match)
class FaixaPreco(Base):
    __tablename__ = "faixas_preco"

    id: Mapped[int] = mapped_column(primary_key=True)
    edital_id: Mapped[int] = mapped_column(ForeignKey("editais.id"), unique=True)
    minimo: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    ideal: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    maximo: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    confiavel: Mapped[bool] = mapped_column(default=False)
    amostra: Mapped[int] = mapped_column(default=0)
    criado_em: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    edital: Mapped["Edital"] = relationship()


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("cliente_id", "edital_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    edital_id: Mapped[int] = mapped_column(ForeignKey("editais.id"))
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    criado_em: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    alertas: Mapped[list["Alerta"]] = relationship(back_populates="match")
    edital: Mapped["Edital"] = relationship()
    cliente: Mapped["Cliente"] = relationship()


class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    canal: Mapped[CanalAlerta]
    status: Mapped[StatusAlerta] = mapped_column(default=StatusAlerta.pendente)
    enviado_em: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    match: Mapped["Match"] = relationship(back_populates="alertas")
