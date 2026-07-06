from __future__ import annotations

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str


class UserRead(BaseModel):
    id: int
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    password: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginPayload(BaseModel):
    username: str
    password: str


# --- Programmes / Batiments / Lots ---


class ProgrammeCreate(BaseModel):
    nom: str
    ville: str | None = None
    adresse: str | None = None
    date_permis_depose: str | None = None
    date_permis_accepte: str | None = None
    responsable_technique: str | None = None
    notaire: str | None = None
    syndic: str | None = None
    architecte: str | None = None
    geometre: str | None = None
    date_demarrage_travaux: str | None = None
    actable: bool | None = None
    disponible: bool | None = None
    numero_permis: str | None = None
    date_livraison_prevue: str | None = None
    date_lancement_commercial: str | None = None
    financement: str | None = None
    signature_notaire: str | None = None
    ca_bilan: float | None = None
    gfa_objectif: float | None = None
    achevement_fondations: str | None = None
    achevement_rdc: str | None = None
    achevement_plancher_haut: str | None = None
    mise_hors_eau: str | None = None
    cloisonnement: str | None = None
    immeuble: str | None = None
    livraison: str | None = None


class ProgrammeRead(BaseModel):
    id: int
    nom: str
    ville: str | None = None
    adresse: str | None = None
    date_permis_depose: str | None = None
    date_permis_accepte: str | None = None
    responsable_technique: str | None = None
    notaire: str | None = None
    syndic: str | None = None
    architecte: str | None = None
    geometre: str | None = None
    date_demarrage_travaux: str | None = None
    actable: bool | None = None
    disponible: bool | None = None
    numero_permis: str | None = None
    date_livraison_prevue: str | None = None
    date_lancement_commercial: str | None = None
    financement: str | None = None
    signature_notaire: str | None = None
    ca_bilan: float | None = None
    gfa_objectif: float | None = None
    lots_count: int | None = None
    ca_total: float | None = None
    ca_realise: float | None = None
    ca_restant: float | None = None
    achevement_fondations: str | None = None
    achevement_rdc: str | None = None
    achevement_plancher_haut: str | None = None
    mise_hors_eau: str | None = None
    cloisonnement: str | None = None
    immeuble: str | None = None
    livraison: str | None = None
    model_config = ConfigDict(from_attributes=True)




class BatimentCreate(BaseModel):
    programme_id: int
    nom: str
    nb_etages: int | None = None
    nb_lots_prevus: int | None = None
    description: str | None = None


class BatimentRead(BaseModel):
    id: int
    programme_id: int
    nom: str
    nb_etages: int | None = None
    nb_lots_prevus: int | None = None
    description: str | None = None
    model_config = ConfigDict(from_attributes=True)




class LotCreate(BaseModel):
    batiment_id: int
    client_id: int | None = None
    lot: str | None = None
    niveau: str | None = None
    type: str | None = None
    surface_sol: float | None = None
    sha_m2: float | None = None
    orientation: str | None = None
    garage: bool | None = None
    parking1: bool | None = None
    parking2: bool | None = None
    cave: bool | None = None
    jardin: float | None = None
    terrasse: float | None = None
    prix_logement: float | None = None
    prix_stationnement: float | None = None
    prix_total: float | None = None
    prix_m2_appartement: float | None = None
    prix_m2_appart_parking: float | None = None
    acquereur: str | None = None
    statut: str | None = None


class LotUpdate(BaseModel):
    client_id: int | None = None
    lot: str | None = None
    niveau: str | None = None
    type: str | None = None
    surface_sol: float | None = None
    sha_m2: float | None = None
    orientation: str | None = None
    garage: bool | None = None
    parking1: bool | None = None
    parking2: bool | None = None
    cave: bool | None = None
    jardin: float | None = None
    terrasse: float | None = None
    prix_logement: float | None = None
    prix_stationnement: float | None = None
    prix_total: float | None = None
    prix_m2_appartement: float | None = None
    prix_m2_appart_parking: float | None = None
    acquereur: str | None = None
    statut: str | None = None


class LotRead(BaseModel):
    id: int
    batiment_id: int
    client_id: int | None = None
    lot: str | None = None
    niveau: str | None = None
    type: str | None = None
    surface_sol: float | None = None
    sha_m2: float | None = None
    orientation: str | None = None
    garage: bool | None = None
    parking1: bool | None = None
    parking2: bool | None = None
    cave: bool | None = None
    jardin: float | None = None
    terrasse: float | None = None
    prix_logement: float | None = None
    prix_stationnement: float | None = None
    prix_total: float | None = None
    prix_m2_appartement: float | None = None
    prix_m2_appart_parking: float | None = None
    acquereur: str | None = None
    statut: str
    programme_name: str | None = None
    client_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


# --- Clients ---

class ClientCreate(BaseModel):
    civility: str | None = None
    type: str | None = "prospect"
    last_name: str
    first_name: str
    address: str | None = None
    address2: str | None = None
    phone: str | None = None
    phone2: str | None = None
    email: EmailStr | None = None
    email2: EmailStr | None = None
    origin: str | None = None
    partner_id: int | None = None
    partner: "ClientCreate | None" = None


class ClientUpdate(BaseModel):
    civility: str | None = None
    type: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    address: str | None = None
    address2: str | None = None
    phone: str | None = None
    phone2: str | None = None
    email: EmailStr | None = None
    email2: EmailStr | None = None
    origin: str | None = None
    partner_id: int | None = None


class ClientPartnerRead(BaseModel):
    id: int
    civility: str | None = None
    type: str | None = None
    last_name: str
    first_name: str
    address: str | None = None
    address2: str | None = None
    phone: str | None = None
    phone2: str | None = None
    email: EmailStr | None = None
    email2: EmailStr | None = None
    origin: str | None = None
    partner_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


class ClientRead(BaseModel):
    id: int
    civility: str | None = None
    type: str | None = None
    last_name: str
    first_name: str
    address: str | None = None
    address2: str | None = None
    phone: str | None = None
    phone2: str | None = None
    email: EmailStr | None = None
    email2: EmailStr | None = None
    origin: str | None = None
    partner_id: int | None = None
    partner: ClientPartnerRead | None = None
    # For Clients page convenience (flattened association row)
    programme_id: int | None = None
    programme_name: str | None = None
    lot_id: int | None = None
    lot_label: str | None = None
    model_config = ConfigDict(from_attributes=True)


ClientCreate.model_rebuild()


class ClientBasic(BaseModel):
    id: int
    civility: str | None = None
    type: str | None = None
    last_name: str
    first_name: str
    email: EmailStr | None = None




# --- Annexes ---

class AnnexeCreate(BaseModel):
    type: str   # "Garage" | "Carport" | "Parking" | "Cave"
    numero: str | None = None


class AnnexeRead(BaseModel):
    id: int
    lot_id: int
    type: str
    numero: str | None = None
    model_config = ConfigDict(from_attributes=True)


# --- Dossiers acquéreurs ---

class PersonneCreate(BaseModel):
    civility: str | None = None
    last_name: str
    first_name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    address2: str | None = None
    origin: str | None = None


class PersonneRead(BaseModel):
    id: int
    civility: str | None = None
    last_name: str
    first_name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    address2: str | None = None
    origin: str | None = None
    model_config = ConfigDict(from_attributes=True)


class DossierCreate(BaseModel):
    type: str  # "solo" | "couple"
    programme_id: int
    lot_id: int | None = None
    personne1: PersonneCreate
    personne2: PersonneCreate | None = None


class DossierUpdate(BaseModel):
    type: str | None = None
    lot_id: int | None = None
    programme_id: int | None = None
    personne1: PersonneCreate | None = None
    personne2: PersonneCreate | None = None


class DossierRead(BaseModel):
    id: int
    type: str
    programme_id: int
    programme_name: str | None = None
    lot_id: int | None = None
    lot_label: str | None = None
    lot_statut: str | None = None
    noms: str  # "Martin Jean" ou "Martin Jean + Dupont Marie"
    clients: list[PersonneRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class LotsStatistics(BaseModel):
    lots_total: int
    actes: int
    reservations: int
    options: int
    libres: int
    ca_total: float
    ca_actes: float
    ca_reservations: float
