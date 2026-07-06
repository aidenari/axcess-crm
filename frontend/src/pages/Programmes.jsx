import { useEffect, useState } from 'react'
import api from '../api/axios'
import Modal from '../components/Modal'
import ProgrammeForm from '../components/ProgrammeForm.jsx'
import { isReadOnly } from '../utils/auth'

export default function Programmes() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [openEdit, setOpenEdit] = useState(false)
  const [editing, setEditing] = useState(false)
  const [current, setCurrent] = useState(null)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/programmes')
      setItems(data || [])
    } catch (e) {
      setError('Impossible de charger les programmes')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const createProgramme = async (payload) => {
    setSubmitting(true)
    try {
      await api.post('/programmes', payload)
      setOpen(false)
      load()
    } catch { alert('Erreur lors de la creation') } finally { setSubmitting(false) }
  }

  const openEditModal = async (id) => {
    try {
      const { data } = await api.get(`/programmes/${id}`)
      setCurrent(data)
      setOpenEdit(true)
    } catch { alert('Impossible de charger le programme') }
  }

  const update = async (id, payload) => {
    setEditing(true)
    try {
      await api.put(`/programmes/${id}`, payload)
      setOpenEdit(false)
      setCurrent(null)
      load()
    } catch { alert('Erreur lors de la modification') } finally { setEditing(false) }
  }

  const removeItem = async (id) => {
    if (!confirm('Supprimer ce programme ?')) return
    try {
      await api.delete(`/programmes/${id}`)
      setItems(items.filter(i => i.id !== id))
    } catch { alert('Erreur lors de la suppression') }
  }

  const formatMoney = (value) =>
    (value || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

  const formatAdresse = (p) => {
    const parts = [p.adresse, p.ville].filter(Boolean)
    return parts.length ? parts.join(' ') : '-'
  }

  const totals = items.reduce((acc, p) => {
    acc.lots += p.lots_count ?? 0
    acc.ca_total += p.ca_total || 0
    acc.ca_realise += p.ca_realise || 0
    acc.ca_restant += p.ca_restant || 0
    acc.ca_bilan += p.ca_bilan || 0
    return acc
  }, { lots: 0, ca_total: 0, ca_realise: 0, ca_restant: 0, ca_bilan: 0 })

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Programmes</h1>
        {!isReadOnly() && (
          <button className="btn" onClick={() => setOpen(true)}>Creer un nouveau programme</button>
        )}
      </div>
      {error && <div className="text-red-600 mb-3 text-sm">{error}</div>}
      {loading ? (
        <div>Chargement...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border">
            <thead className="bg-gray-50">
              <tr className="text-left">
                <th className="p-2 border">Nom</th>
                <th className="p-2 border">Adresse</th>
                <th className="p-2 border">Nb lots</th>
                <th className="p-2 border">CA total</th>
                <th className="p-2 border">CA Bilan</th>
                <th className="p-2 border">Objectif GFA</th>
                <th className="p-2 border">CA réalisé</th>
                <th className="p-2 border">CA restant</th>
                <th className="p-2 border">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(p => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="p-2 border font-medium">{p.nom || p.name}</td>
                  <td className="p-2 border">{formatAdresse(p)}</td>
                  <td className="p-2 border">{p.lots_count ?? 0}</td>
                  <td className="p-2 border">{formatMoney(p.ca_total)}</td>
                  <td className="p-2 border">{formatMoney(p.ca_bilan || 0)}</td>
                  <td className="p-2 border">{p.gfa_objectif === null || p.gfa_objectif === undefined ? '-' : p.gfa_objectif.toLocaleString('fr-FR')}</td>
                  <td className="p-2 border">
                    <div className="font-medium">{formatMoney(p.ca_realise)}</div>
                    <div className="mt-1 h-2 rounded-full bg-gray-100">
                      <div
                        className="h-2 rounded-full bg-blue-600"
                        style={{ width: `${p.ca_total ? Math.min(100, Math.round((p.ca_realise / p.ca_total) * 100)) : 0}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {p.ca_total ? Math.round((p.ca_realise / p.ca_total) * 100) : 0}%
                    </div>
                  </td>
                  <td className="p-2 border">{formatMoney(p.ca_restant)}</td>
                  <td className="p-2 border">
                    <div className="flex items-center gap-3">
                      {!isReadOnly() && (
                        <>
                          <button className="text-blue-700 hover:underline" onClick={() => openEditModal(p.id)}>Modifier</button>
                          <button className="text-red-600 hover:underline" onClick={() => removeItem(p.id)}>Supprimer</button>
                        </>
                      )}
                      <button className="text-gray-700 hover:underline" onClick={() => window.location.assign('/grilles-de-prix/' + p.id)}>Grille de prix</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-gray-50">
              <tr className="text-left font-semibold">
                <td className="p-2 border">Total</td>
                <td className="p-2 border">-</td>
                <td className="p-2 border">{totals.lots}</td>
                <td className="p-2 border">{formatMoney(totals.ca_total)}</td>
                <td className="p-2 border">{formatMoney(totals.ca_bilan)}</td>
                <td className="p-2 border">-</td>
                <td className="p-2 border">{formatMoney(totals.ca_realise)}</td>
                <td className="p-2 border">{formatMoney(totals.ca_restant)}</td>
                <td className="p-2 border">-</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      <Modal open={open} title="Creer un programme" onClose={() => setOpen(false)}>
        <ProgrammeForm onSubmit={createProgramme} submitting={submitting} />
      </Modal>
      <Modal open={openEdit} title="Modifier le programme" onClose={() => setOpenEdit(false)}>
        {current && (
          <ProgrammeForm initial={current} onSubmit={(payload) => update(current.id, payload)} submitting={editing} />
        )}
      </Modal>
    </div>
  )
}
