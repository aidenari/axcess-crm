import React from 'react'
import { formatDate } from '../utils/formatDate'

function Row({ label, value }) {
  return (
    <div className="grid grid-cols-3 gap-2 py-1">
      <div className="text-sm text-gray-500 col-span-1">{label}</div>
      <div className="text-sm col-span-2">{value || '—'}</div>
    </div>
  )
}

export default function ProgrammeHeader({ programme }) {
  const p = programme || {}
  return (
    <div className="card">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Row label="Ville" value={p.ville || p.city} />
          <Row label="Adresse" value={p.adresse || p.address} />
          <Row label="Permis déposé" value={formatDate(p.date_permis_depose)} />
          <Row label="Permis accepté" value={formatDate(p.date_permis_accepte)} />
          <Row label="Architecte" value={p.architecte || p.architect} />
          <Row label="Responsable technique" value={p.responsable_technique} />
          <Row label="Financement" value={p.financement} />
        </div>
        <div>
          <Row label="Notaire" value={p.notaire} />
          <Row label="Syndic" value={p.syndic} />
          <Row label="Géomètre" value={p.geometre} />
          <Row label="Démarrage travaux" value={formatDate(p.date_demarrage_travaux)} />
          <Row label="Livraison prévue" value={formatDate(p.date_livraison_prevue)} />
          <Row label="Lancement commercial" value={formatDate(p.date_lancement_commercial || p.launch_date)} />
          <Row label="Signature notaire" value={formatDate(p.signature_notaire)} />
        </div>
      </div>
    </div>
  )
}

