import React, { useState } from 'react'
import Modal from './Modal.jsx'
import api from '../api/axios'
import { Trash2 } from 'lucide-react'

const ANNEXE_TYPES = ['Garage', 'Carport', 'Parking', 'Cave']

const empty = (batimentId) => ({
  batiment_id: batimentId,
  lot: '',
  niveau: '',
  type: '',
  surface_sol: '',
  sha_m2: '',
  orientation: '',
  jardin: '',
  terrasse: '',
  prix_logement: '',
  prix_stationnement: '',
  prix_total: '',
  prix_m2_appartement: '',
  prix_m2_appart_parking: '',
  acquereur: '',
  statut: 'Libre'
})

export default function CreateLotModal({ open, onClose, batimentId, onCreated }) {
  const [form, setForm] = useState(empty(batimentId))
  const [loading, setLoading] = useState(false)

  // Annexes en attente (créées après le lot)
  const [pendingAnnexes, setPendingAnnexes] = useState([])
  const [newAnnexeType, setNewAnnexeType] = useState('Garage')
  const [newAnnexeNumero, setNewAnnexeNumero] = useState('')

  const onChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const addPendingAnnexe = () => {
    setPendingAnnexes(prev => [
      ...prev,
      { _key: Date.now(), type: newAnnexeType, numero: newAnnexeNumero.trim() || null }
    ])
    setNewAnnexeNumero('')
  }

  const removePendingAnnexe = (key) => {
    setPendingAnnexes(prev => prev.filter(a => a._key !== key))
  }

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        ...form,
        batiment_id: batimentId,
        surface_sol: form.surface_sol ? Number(form.surface_sol) : null,
        sha_m2: form.sha_m2 ? Number(form.sha_m2) : null,
        jardin: form.jardin ? Number(form.jardin) : null,
        terrasse: form.terrasse ? Number(form.terrasse) : null,
        prix_logement: form.prix_logement ? Number(form.prix_logement) : null,
        prix_stationnement: form.prix_stationnement ? Number(form.prix_stationnement) : null,
        prix_total: form.prix_total ? Number(form.prix_total) : null,
        prix_m2_appartement: form.prix_m2_appartement ? Number(form.prix_m2_appartement) : null,
        prix_m2_appart_parking: form.prix_m2_appart_parking ? Number(form.prix_m2_appart_parking) : null,
      }
      const { data: newLot } = await api.post('/lots', payload)

      // Créer les annexes en attente
      const createdAnnexes = []
      for (const a of pendingAnnexes) {
        try {
          const { data: ann } = await api.post(`/lots/${newLot.id}/annexes`, {
            type: a.type,
            numero: a.numero,
          })
          createdAnnexes.push(ann)
        } catch (e) {
          console.error('Erreur création annexe', e)
        }
      }

      onCreated?.({ ...newLot, annexes: createdAnnexes })
      onClose?.()
      setForm(empty(batimentId))
      setPendingAnnexes([])
      setNewAnnexeNumero('')
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Créer un lot">
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm mb-1">Lot</label>
          <input className="input" name="lot" value={form.lot} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Niveau</label>
          <input className="input" name="niveau" value={form.niveau} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Type</label>
          <input className="input" name="type" value={form.type} onChange={onChange} placeholder="T2, T3..." />
        </div>
        <div>
          <label className="block text-sm mb-1">Surface sol</label>
          <input className="input" type="number" name="surface_sol" value={form.surface_sol} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">SHA m²</label>
          <input className="input" type="number" step="0.01" name="sha_m2" value={form.sha_m2} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Orientation</label>
          <input className="input" name="orientation" value={form.orientation} onChange={onChange} />
        </div>

        {/* Annexes manager */}
        <div className="col-span-2 border rounded-lg p-3 bg-gray-50">
          <div className="text-sm font-medium mb-2">Annexes</div>
          {pendingAnnexes.length > 0 && (
            <div className="space-y-1 mb-3">
              {pendingAnnexes.map(a => (
                <div key={a._key} className="flex items-center gap-2 text-sm bg-white border rounded px-2 py-1">
                  <span className="font-medium w-20">{a.type}</span>
                  <span className="text-gray-500 flex-1">{a.numero || <span className="italic text-gray-300">Sans numéro</span>}</span>
                  <button
                    type="button"
                    className="text-red-400 hover:text-red-600 p-0.5 rounded"
                    onClick={() => removePendingAnnexe(a._key)}
                    title="Retirer"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2">
            <select
              className="input text-sm flex-shrink-0 w-32"
              value={newAnnexeType}
              onChange={e => setNewAnnexeType(e.target.value)}
            >
              {ANNEXE_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
            <input
              className="input text-sm flex-1"
              placeholder="Numéro (ex: 12, B3)"
              value={newAnnexeNumero}
              onChange={e => setNewAnnexeNumero(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addPendingAnnexe() } }}
            />
            <button
              type="button"
              className="btn text-sm px-3 py-1.5 whitespace-nowrap"
              onClick={addPendingAnnexe}
            >
              + Ajouter
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm mb-1">Jardin (m²)</label>
          <input className="input" type="number" step="0.01" name="jardin" value={form.jardin} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Terrasse (m²)</label>
          <input className="input" type="number" step="0.01" name="terrasse" value={form.terrasse} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Prix logement</label>
          <input className="input" type="number" name="prix_logement" value={form.prix_logement} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Prix stationnement</label>
          <input className="input" type="number" name="prix_stationnement" value={form.prix_stationnement} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Prix total</label>
          <input className="input" type="number" name="prix_total" value={form.prix_total} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Acquéreur</label>
          <input className="input" name="acquereur" value={form.acquereur} onChange={onChange} />
        </div>
        <div>
          <label className="block text-sm mb-1">Statut</label>
          <select className="input" name="statut" value={form.statut} onChange={onChange}>
            <option>Libre</option>
            <option>Option</option>
            <option>Réservation</option>
            <option>Acté</option>
          </select>
        </div>
        <div className="col-span-2 text-right">
          <button className="btn" disabled={loading}>{loading ? 'Création...' : 'Créer'}</button>
        </div>
      </form>
    </Modal>
  )
}
