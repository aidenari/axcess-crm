import React, { useState } from 'react'
import Modal from './Modal.jsx'
import api from '../api/axios'

export default function CreateBatimentModal({ open, onClose, programmeId, onCreated }) {
  const [form, setForm] = useState({ nom: '', nb_etages: '', nb_lots_prevus: '', description: '' })
  const [loading, setLoading] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (!programmeId) return
    setLoading(true)
    try {
      const payload = {
        programme_id: programmeId,
        nom: form.nom,
        nb_etages: form.nb_etages ? Number(form.nb_etages) : null,
        nb_lots_prevus: form.nb_lots_prevus ? Number(form.nb_lots_prevus) : null,
        description: form.description || null
      }
      const { data } = await api.post('/batiments', payload)
      onCreated?.(data)
      onClose?.()
      setForm({ nom: '', nb_etages: '', nb_lots_prevus: '', description: '' })
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  return (
    <Modal open={open} onClose={onClose} title="Créer un bâtiment">
      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm mb-1">Nom</label>
          <input className="input" name="nom" value={form.nom} onChange={onChange} placeholder="A, B, C" required />
        </div>
        <div>
          <label className="block text-sm mb-1">Nb étages</label>
          <input className="input" name="nb_etages" value={form.nb_etages} onChange={onChange} type="number" />
        </div>
        <div>
          <label className="block text-sm mb-1">Nb lots prévus</label>
          <input className="input" name="nb_lots_prevus" value={form.nb_lots_prevus} onChange={onChange} type="number" />
        </div>
        <div className="col-span-2">
          <label className="block text-sm mb-1">Description</label>
          <textarea className="input" name="description" value={form.description} onChange={onChange} />
        </div>
        <div className="col-span-2 text-right">
          <button className="btn" disabled={loading}>{loading ? 'Création...' : 'Créer'}</button>
        </div>
      </form>
    </Modal>
  )
}

