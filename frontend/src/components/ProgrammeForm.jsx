import React, { useState } from 'react'

const empty = {
  nom: '',
  ville: '',
  adresse: '',
  ca_bilan: '',
  gfa_objectif: '',
  date_permis_depose: '',
  date_permis_accepte: '',
  responsable_technique: '',
  notaire: '',
  syndic: '',
  architecte: '',
  geometre: '',
  date_demarrage_travaux: '',
  actable: false,
  disponible: false,
  numero_permis: '',
  date_livraison_prevue: '',
  date_lancement_commercial: '',
  financement: '',
  signature_notaire: '',
  achevement_fondations: '',
  achevement_rdc: '',
  achevement_plancher_haut: '',
  mise_hors_eau: '',
  cloisonnement: '',
  immeuble: '',
  livraison: ''
}

export default function ProgrammeForm({ onSubmit, initial = empty, submitting = false }) {
  const [form, setForm] = useState({ ...empty, ...initial })

  const onChange = (e) => {
    const { name, type, checked, value } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const submit = async (e) => {
    e.preventDefault()
    const clean = Object.fromEntries(
      Object.entries(form).map(([k, v]) => [k, v === '' ? null : v])
    )
    onSubmit?.(clean)
  }

  return (
    <form onSubmit={submit} className="grid grid-cols-2 gap-3 max-h-[70vh] overflow-auto pr-1">
      <div className="col-span-2">
        <label className="block text-sm mb-1">Nom</label>
        <input className="input" name="nom" value={form.nom} onChange={onChange} required />
      </div>
      <div>
        <label className="block text-sm mb-1">Ville</label>
        <input className="input" name="ville" value={form.ville} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Adresse</label>
        <input className="input" name="adresse" value={form.adresse} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">CA bilan</label>
        <input className="input" type="number" step="0.01" name="ca_bilan" value={form.ca_bilan} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Objectif GFA</label>
        <input className="input" type="number" step="0.01" name="gfa_objectif" value={form.gfa_objectif} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Permis déposé</label>
        <input className="input" type="date" lang="fr-FR" name="date_permis_depose" value={form.date_permis_depose} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Permis accepté</label>
        <input className="input" type="date" lang="fr-FR" name="date_permis_accepte" value={form.date_permis_accepte} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Responsable technique</label>
        <input className="input" name="responsable_technique" value={form.responsable_technique} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Notaire</label>
        <input className="input" name="notaire" value={form.notaire} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Syndic</label>
        <input className="input" name="syndic" value={form.syndic} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Architecte</label>
        <input className="input" name="architecte" value={form.architecte} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Géomètre</label>
        <input className="input" name="geometre" value={form.geometre} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Démarrage travaux</label>
        <input className="input" type="date" lang="fr-FR" name="date_demarrage_travaux" value={form.date_demarrage_travaux} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Livraison prévue</label>
        <input className="input" type="text" name="date_livraison_prevue" value={form.date_livraison_prevue} onChange={onChange} placeholder="JJ/MM/AAAA" />
      </div>
      <div>
        <label className="block text-sm mb-1">Lancement commercial</label>
        <input className="input" type="text" name="date_lancement_commercial" value={form.date_lancement_commercial} onChange={onChange} placeholder="JJ/MM/AAAA" />
      </div>
      <div>
        <label className="block text-sm mb-1">Financement</label>
        <input className="input" name="financement" value={form.financement} onChange={onChange} />
      </div>
      <div>
        <label className="block text-sm mb-1">Signature notaire</label>
        <input className="input" type="text" name="signature_notaire" value={form.signature_notaire} onChange={onChange} placeholder="JJ/MM/AAAA" />
      </div>
      <div>
        <label className="block text-sm mb-1">Numéro permis</label>
        <input className="input" name="numero_permis" value={form.numero_permis} onChange={onChange} />
      </div>
      <div className="flex items-center gap-3 col-span-2">
        <label className="flex items-center gap-2"><input type="checkbox" name="actable" checked={form.actable} onChange={onChange} /> Actable</label>
        <label className="flex items-center gap-2"><input type="checkbox" name="disponible" checked={form.disponible} onChange={onChange} /> Disponible</label>
      </div>
      <div className="col-span-2 text-right mt-2">
        <button className="btn" disabled={submitting}>{submitting ? 'Envoi...' : 'Enregistrer'}</button>
      </div>
    </form>
  )
}

