from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True, default="commercial")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r}>"


class Programme(Base):
    __tablename__ = "programmes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(255))
    ville: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adresse: Mapped[str | None] = mapped_column(String(255), nullable=True)

    date_permis_depose: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_permis_accepte: Mapped[str | None] = mapped_column(String(20), nullable=True)
    responsable_technique: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notaire: Mapped[str | None] = mapped_column(String(255), nullable=True)
    syndic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    architecte: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geometre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_demarrage_travaux: Mapped[str | None] = mapped_column(String(20), nullable=True)
    actable: Mapped[bool] = mapped_column(default=False)
    disponible: Mapped[bool] = mapped_column(default=False)
    numero_permis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_livraison_prevue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_lancement_commercial: Mapped[str | None] = mapped_column(String(20), nullable=True)
    financement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signature_notaire: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ca_bilan: Mapped[float | None] = mapped_column(nullable=True)
    gfa_objectif: Mapped[float | None] = mapped_column(nullable=True)

    # jalons (facultatifs sous forme de dates/strings)
    achevement_fondations: Mapped[str | None] = mapped_column(String(20), nullable=True)
    achevement_rdc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    achevement_plancher_haut: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mise_hors_eau: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cloisonnement: Mapped[str | None] = mapped_column(String(20), nullable=True)
    immeuble: Mapped[str | None] = mapped_column(String(20), nullable=True)
    livraison: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())

    batiments: Mapped[list[Batiment]] = relationship("Batiment", back_populates="programme", cascade="all, delete-orphan")


class Batiment(Base):
    __tablename__ = "batiments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    programme_id: Mapped[int] = mapped_column(ForeignKey("programmes.id", ondelete="CASCADE"), index=True)
    nom: Mapped[str] = mapped_column(String(50))
    nb_etages: Mapped[int | None] = mapped_column(nullable=True)
    nb_lots_prevus: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    programme: Mapped[Programme] = relationship("Programme", back_populates="batiments")
    lots: Mapped[list[Lot]] = relationship("Lot", back_populates="batiment", cascade="all, delete-orphan")


class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    batiment_id: Mapped[int] = mapped_column(ForeignKey("batiments.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)

    lot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    niveau: Mapped[str | None] = mapped_column(String(50), nullable=True)
    type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    surface_sol: Mapped[float | None] = mapped_column(nullable=True)
    sha_m2: Mapped[float | None] = mapped_column(nullable=True)
    orientation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    garage: Mapped[bool] = mapped_column(default=False)
    parking1: Mapped[bool] = mapped_column(default=False)
    parking2: Mapped[bool] = mapped_column(default=False)
    cave: Mapped[bool] = mapped_column(default=False)
    jardin: Mapped[float | None] = mapped_column(nullable=True)
    terrasse: Mapped[float | None] = mapped_column(nullable=True)

    prix_logement: Mapped[float | None] = mapped_column(nullable=True)
    prix_stationnement: Mapped[float | None] = mapped_column(nullable=True)
    prix_total: Mapped[float | None] = mapped_column(nullable=True)
    prix_m2_appartement: Mapped[float | None] = mapped_column(nullable=True)
    prix_m2_appart_parking: Mapped[float | None] = mapped_column(nullable=True)

    acquereur: Mapped[str | None] = mapped_column(String(255), nullable=True)
    statut: Mapped[str] = mapped_column(String(20), default="Libre")

    batiment: Mapped[Batiment] = relationship("Batiment", back_populates="lots")
    client: Mapped[Client | None] = relationship("Client", back_populates="lots")
    dossier: Mapped[DossierAcquereur | None] = relationship(
        "DossierAcquereur", back_populates="lot", uselist=False, lazy="selectin"
    )
    annexes: Mapped[list[Annexe]] = relationship(
        "Annexe", back_populates="lot", cascade="all, delete-orphan", lazy="selectin"
    )


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    civility: Mapped[str | None] = mapped_column(String(20), nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="prospect")
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone2: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    email2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dossier_id: Mapped[int | None] = mapped_column(
        ForeignKey("dossier_acquereur.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    lots: Mapped[list[Lot]] = relationship("Lot", back_populates="client")
    dossier: Mapped[DossierAcquereur | None] = relationship("DossierAcquereur", back_populates="clients")
    partner: Mapped["Client | None"] = relationship("Client", remote_side="Client.id", foreign_keys=[partner_id])


class DossierAcquereur(Base):
    __tablename__ = "dossier_acquereur"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(10), default="solo")  # "solo" | "couple"
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("lots.id", ondelete="SET NULL"), nullable=True, index=True
    )
    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    programme: Mapped[Programme] = relationship("Programme")
    lot: Mapped[Lot | None] = relationship("Lot", back_populates="dossier")
    clients: Mapped[list[Client]] = relationship(
        "Client", back_populates="dossier", cascade="all, delete-orphan", lazy="selectin"
    )


class Annexe(Base):
    __tablename__ = "annexes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lots.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(50))   # "Garage" | "Carport" | "Parking" | "Cave"
    numero: Mapped[str | None] = mapped_column(String(50), nullable=True)

    lot: Mapped[Lot] = relationship("Lot", back_populates="annexes")
