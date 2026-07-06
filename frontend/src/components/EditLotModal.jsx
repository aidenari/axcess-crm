import React, { useEffect, useState } from 'react'
import Modal from './Modal.jsx'
import ClientDrawer from './ClientDrawer.jsx'
import api from '../api/axios'
import { Trash2 } from 'lucide-react'

const ANNEXE_TYPES = ['Garage', 'Carport', 'Parking', 'Cave']

function toIsoDate(v) {
  if (!v) return ''
  if (/^\d{4}-\d{2}-\d{2}/.test(v)) return v.slice(0, 10)
  const m = String(v).match(/(\d{2})\/(\d{2})\/(\d{4})/)
  if (m) return `${m[3]}-${m[2]}-${m[1]}`
  return ''
}

const toForm = (lot) => ({
  lot: lot?.lot ?? '',
  niveau: lot?.niveau ?? '',
  type: lot?.type ?? '',
  surface_sol: lot?.surface_sol ?? '',
  sha_m2: lot?.sha_m2 ?? '',
  orientation: lot?.orientation ?? '',
  hasJardin: lot?.jardin != null && lot.jardin !== '' && Number(lot.jardin) > 0,
  hasTerrasse: lot?.terrasse != null && lot.terrasse !== '' && Number(lot.terrasse) > 0,
  jardin: lot?.jardin ?? '',
  terrasse: lot?.terrasse ?? '',
  prix_logement: lot?.prix_logement ?? '',
  prix_stationnement: lot?.prix_stationnement ?? '',
  prix_total: lot?.prix_total ?? '',
  prix_m2_appartement: lot?.prix_m2_appartement ?? '',
  prix_m2_appart_parking: lot?.prix_m2_appart_parking ?? '',
  acquereur: lot?.acquereur ?? '',
  statut: lot?.statut ?? 'Libre',
  date_reservation: toIsoDate(lot?.date_reservation),
  date_acte: toIsoDate(lot?.date_acte),
  client_ids: lot?.acquereurs?.length
    ? (lot.acquereurs_ids ?? [])
    : (lot?.client_id ? [lot.client_id] : []),
})

export default function EditLotModal({ open, onClose, lot, onSaved, onDeleted }) {
  const [form, setForm] = useState(toForm(lot))
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState([])
  const [showClientDrawer, setShowClientDrawer] = useState(false)
  const [clientSearch, setClientSearch] = useState('')

  // Annexes state
  const [annexes, setAnnexes] = useState([])
  const [newAnnexeType, setNewAnnexeType] = useState('Garage')
  const [newAnnexeNumero, setNewAnnexeNumero] = useState('')
  const [annexeAdding, setAnnexeAdding] = useState(false)

  useEffect(() => {
    setForm(toForm(lot))
    setAnnexes(lot?.annexes ?? [])
  }, [lot?.id])

  useEffect(() => {
    if (!open) return
    const loadClients = async () => {
      try {
        const { data } = await api.get('/clients')
        setClients(data || [])
      } catch (e) {
        console.error("Failed to load clients", e)
      }
    }
    loadClients()
  }, [open])

  const onChange = (e) => {
    const { name, value, type, checked } = e.target
    const newVal = type === 'checkbox' ? checked : value

    setForm(prev => {
      const next = { ...prev, [name]: newVal }

      // Clear m² when unchecking jardin/terrasse
      if (name === 'hasJardin' && !newVal) next.jardin = ''
      if (name === 'hasTerrasse' && !newVal) next.terrasse = ''

      // Auto-calculation: Prix Logement = Total - Stationnement
      if (name === 'prix_total' || name === 'prix_stationnement') {
        const total = parseFloat(name === 'prix_total' ? newVal : next.prix_total) || 0
        const parking = parseFloat(name === 'prix_stationnement' ? newVal : next.prix_stationnement) || 0
        next.prix_logement = total - parking
      }
      return next
    })
  }

  const addAnnexe = async () => {
    if (!lot?.id) return
    setAnnexeAdding(true)
    try {
      const { data } = await api.post(`/lots/${lot.id}/annexes`, {
        type: newAnnexeType,
        numero: newAnnexeNumero.trim() || null,
      })
      setAnnexes(prev => [...prev, data])
      setNewAnnexeNumero('')
    } catch (e) {
      console.error(e)
    } finally {
      setAnnexeAdding(false)
    }
  }

  const removeAnnexe = async (annexeId) => {
    try {
      await api.delete(`/annexes/${annexeId}`)
      setAnnexes(prev => prev.filter(a => a.id !== annexeId))
    } catch (e) {
      console.error(e)
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!lot?.id) return
    setLoading(true)
    try {
      const payload = {
        ...form,
        client_id: form.client_ids?.[0] ?? null,
        client_ids: form.client_ids.map(Number),
        surface_sol: form.surface_sol !== '' ? Number(form.surface_sol) : null,
        sha_m2: form.sha_m2 !== '' ? Number(form.sha_m2) : null,
        jardin: (form.hasJardin && form.jardin !== '') ? Number(form.jardin) : null,
        terrasse: (form.hasTerrasse && form.terrasse !== '') ? Number(form.terrasse) : null,
        prix_logement: form.prix_logement !== '' ? Number(form.prix_logement) : null,
        prix_stationnement: form.prix_stationnement !== '' ? Number(form.prix_stationnement) : null,
        prix_total: form.prix_total !== '' ? Number(form.prix_total) : null,
        prix_m2_appartement: form.prix_m2_appartement !== '' ? Number(form.prix_m2_appartement) : null,
        prix_m2_appart_parking: form.prix_m2_appart_parking !== '' ? Number(form.prix_m2_appart_parking) : null,
        date_reservation: form.date_reservation || null,
        date_acte: form.date_acte || null,
      }

      const { data } = await api.put(`/lots/${lot.id}`, payload)
      onSaved?.({ ...(data || { ...lot, ...payload }), annexes })
      onClose?.()
    } catch (e) {
      console.error(e)
      alert("Une erreur est survenue lors de l'enregistrement.")
    } finally {
      setLoading(false)
    }
  }

  const onDelete = async () => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce lot ? Cette action est irréversible.")) return
    if (!lot?.id) return
    setLoading(true)
    try {
      await api.delete(`/lots/${lot.id}`)
      onDeleted?.(lot.id)
      onClose?.()
    } catch (e) {
      console.error(e)
      alert("Impossible de supprimer le lot.")
    } finally {
      setLoading(false)
    }
  }

  const toggleClient = (id) => {
    setForm(prev => {
      const ids = prev.client_ids.map(Number)
      const nid = Number(id)
      return {
        ...prev,
        client_ids: ids.includes(nid) ? ids.filter(x => x !== nid) : [...ids, nid]
      }
    })
  }

  const onClientCreated = (newClient) => {
    setClients(prev => [...prev, newClient])
    setForm(prev => ({
      ...prev,
      client_ids: [...prev.client_ids, newClient.id],
    }))
    setShowClientDrawer(false)
  }

  return (
    <>
      <Modal open={open} onClose={onClose} title="Modifier le lot">
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
            {annexes.length > 0 && (
              <div className="space-y-1 mb-3">
                {annexes.map(a => (
                  <div key={a.id} className="flex items-center gap-2 text-sm bg-white border rounded px-2 py-1">
                    <span className="font-medium w-20">{a.type}</span>
                    <span className="text-gray-500 flex-1">{a.numero || <span className="italic text-gray-300">Sans numéro</span>}</span>
                    <button
                      type="button"
                      className="text-red-400 hover:text-red-600 p-0.5 rounded"
                      onClick={() => removeAnnexe(a.id)}
                      title="Supprimer"
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
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addAnnexe() } }}
              />
              <button
                type="button"
                className="btn text-sm px-3 py-1.5 whitespace-nowrap"
                onClick={addAnnexe}
                disabled={annexeAdding || !lot?.id}
              >
                + Ajouter
              </button>
            </div>
          </div>
          <div className="flex items-center gap-4 col-span-2 flex-wrap">
            <label className="flex items-center gap-2"><input type="checkbox" name="hasJardin" checked={form.hasJardin} onChange={onChange} /> Jardin</label>
            <label className="flex items-center gap-2"><input type="checkbox" name="hasTerrasse" checked={form.hasTerrasse} onChange={onChange} /> Terrasse</label>
          </div>
          {(form.hasJardin || form.hasTerrasse) && (
            <div className="col-span-2 grid grid-cols-2 gap-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
              {form.hasJardin && (
                <div>
                  <label className="block text-sm mb-1">Jardin (m²)</label>
                  <input className="input" type="number" step="0.01" name="jardin" value={form.jardin} onChange={onChange} placeholder="0.00" autoFocus />
                </div>
              )}
              {form.hasTerrasse && (
                <div>
                  <label className="block text-sm mb-1">Terrasse (m²)</label>
                  <input className="input" type="number" step="0.01" name="terrasse" value={form.terrasse} onChange={onChange} placeholder="0.00" />
                </div>
              )}
            </div>
          )}
          <div>
            <label className="block text-sm mb-1">Prix logement (Calc)</label>
            <input
              className="input bg-gray-100 text-gray-500 cursor-not-allowed"
              type="number"
              name="prix_logement"
              value={form.prix_logement}
              readOnly
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Prix stationnement</label>
            <input className="input" type="number" name="prix_stationnement" value={form.prix_stationnement} onChange={onChange} />
          </div>
          <div>
            <label className="block text-sm mb-1">Prix total</label>
            <input className="input" type="number" name="prix_total" value={form.prix_total} onChange={onChange} />
          </div>

          <div className="col-span-2">
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm">Acquéreurs</label>
              <button
                type="button"
                className="text-xs text-blue-600 hover:underline"
                onClick={() => setShowClientDrawer(true)}
              >
                + Nouveau client
              </button>
            </div>
            <input
              className="input w-full mb-1"
              placeholder="Rechercher un client..."
              value={clientSearch}
              onChange={e => setClientSearch(e.target.value)}
            />
            <div className="border rounded max-h-36 overflow-y-auto bg-white">
              {[...clients]
                .sort((a, b) => (a.last_name || '').localeCompare(b.last_name || ''))
                .filter(c => {
                  if (!clientSearch) return true
                  const q = clientSearch.toLowerCase()
                  return `${c.last_name} ${c.first_name}`.toLowerCase().includes(q)
                })
                .map(c => {
                  const selected = form.client_ids.map(Number).includes(c.id)
                  return (
                    <label
                      key={c.id}
                      className={`flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-gray-50 ${selected ? 'bg-blue-50' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => toggleClient(c.id)}
                      />
                      <span className="text-sm">{c.last_name} {c.first_name}</span>
                    </label>
                  )
                })}
              {clients.length === 0 && (
                <div className="px-3 py-2 text-sm text-gray-400 italic">Aucun client</div>
              )}
            </div>
            {form.client_ids.length > 0 && (
              <div className="mt-1 text-xs text-gray-500">
                {form.client_ids.length} acquéreur{form.client_ids.length > 1 ? 's' : ''} sélectionné{form.client_ids.length > 1 ? 's' : ''}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm mb-1">Statut</label>
            <select className="input" name="statut" value={form.statut} onChange={onChange}>
              <option>Libre</option>
              <option>Option</option>
              <option>Réservé</option>
              <option>Acté</option>
            </select>
          </div>

          <div>
            <label className="block text-sm mb-1">Date de réservation</label>
            <input className="input" type="date" name="date_reservation" value={form.date_reservation} onChange={onChange} />
          </div>
          <div>
            <label className="block text-sm mb-1">Date de signature d'acte</label>
            <input className="input" type="date" name="date_acte" value={form.date_acte} onChange={onChange} />
          </div>

          <div className="col-span-2 flex justify-between items-center mt-4 pt-3 border-t">
            <button
              type="button"
              onClick={onDelete}
              className="px-3 py-2 text-red-600 hover:bg-red-50 rounded border border-transparent hover:border-red-200 transition-colors"
              disabled={loading}
            >
              Supprimer le lot
            </button>
            <div className="flex gap-2">
              <button type="button" onClick={onClose} className="btn bg-white border border-gray-300 text-gray-700 hover:bg-gray-50">Annuler</button>
              <button className="btn bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
                {loading ? 'Enregistrement...' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </form>
      </Modal >
      <ClientDrawer open={showClientDrawer} onClose={() => setShowClientDrawer(false)} onSaved={onClientCreated} />
    </>
  )
}
