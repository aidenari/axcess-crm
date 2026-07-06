import React, { useEffect, useState, useMemo } from 'react'
import api from '../api/axios'
import LotRow from './LotRow.jsx'
import CreateLotModal from './CreateLotModal.jsx'
import EditLotModal from './EditLotModal.jsx'
import EditBatimentModal from './EditBatimentModal.jsx'
import { isReadOnly } from '../utils/auth'
import { Pencil, Trash2 } from 'lucide-react'

export default function GrilleTable({ batiment, filters, onChanged, highlightLotId, onBatimentUpdated, onBatimentDeleted }) {
  const [lots, setLots] = useState([])
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [clients, setClients] = useState([])
  const [editBat, setEditBat] = useState(false)

  const load = async () => {
    try {
      const { data } = await api.get('/lots', { params: { batiment_id: batiment.id } })
      setLots(data || [])
    } catch (e) { console.error(e) }
  }
  useEffect(() => { load() }, [batiment?.id])

  useEffect(() => {
    const loadClients = async () => {
      try {
        const { data } = await api.get('/clients/all')
        setClients(data || [])
      } catch (e) { /* ignore */ }
    }
    loadClients()
  }, [])

  const onUpdate = async (id, patch) => {
    setLots(prev => prev.map(l => l.id === id ? { ...l, ...patch } : l))
    try { await api.put(`/lots/${id}`, patch); onChanged?.() } catch (e) { console.error(e) }
  }

  const addLotLocal = (l) => { setLots(prev => [l, ...prev]); onChanged?.() }

  const niveauOrder = (niveau) => {
    const n = (niveau || '').trim().toUpperCase()
    if (n === 'RDC') return 0
    const m = n.match(/^R\+(\d+)$/)
    if (m) return parseInt(m[1], 10)
    return 999
  }

  const filtered = useMemo(() => {
    return lots
      .filter(l => {
        const okS = filters?.statut === 'Tous' || l.statut === filters.statut
        const okT = filters?.type === 'Tous' || l.type === filters.type
        return okS && okT
      })
      .sort((a, b) => niveauOrder(a.niveau) - niveauOrder(b.niveau))
  }, [lots, filters])

  const caTotal = useMemo(() => filtered.reduce((acc, l) => acc + (Number(l.prix_total) || 0), 0), [filtered])

  const handleDeleteBatiment = async () => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce bâtiment et tous ses lots ?")) return
    try {
      await api.delete(`/batiments/${batiment.id}`)
      onBatimentDeleted?.(batiment.id)
    } catch (e) {
      console.error(e)
      alert("Impossible de supprimer le bâtiment")
    }
  }

  return (
    <div className="bg-white rounded-xl border mb-6">
      <div className="flex items-center justify-between p-3 bg-gray-50 border-b rounded-t-xl">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold">{batiment.nom || batiment.name}</h3>
          {!isReadOnly() && (
            <div className="flex items-center gap-1">
              <button className="p-1 hover:bg-gray-200 rounded text-gray-600" title="Modifier le nom" onClick={() => setEditBat(true)}>
                <Pencil size={16} />
              </button>
              <button className="p-1 hover:bg-red-100 rounded text-red-600" title="Supprimer le bâtiment" onClick={handleDeleteBatiment}>
                <Trash2 size={16} />
              </button>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!isReadOnly() && (
            <button className="px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm" onClick={() => setOpen(true)}>Créer un lot</button>
          )}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead className="bg-gray-100 text-gray-700">
            <tr className="text-left">
              <th className="p-2 border">Lot</th>
              <th className="p-2 border">Niveau</th>
              <th className="p-2 border">Type</th>
              <th className="p-2 border">Surface sol</th>
              <th className="p-2 border">SHA m²</th>
              <th className="p-2 border">Orientation</th>
              <th className="p-2 border">Annexes</th>
              <th className="p-2 border">Jardin</th>
              <th className="p-2 border">Terrasse</th>
              <th className="p-2 border">Prix logement</th>
              <th className="p-2 border">Prix stationnement</th>
              <th className="p-2 border">Prix total</th>
              <th className="p-2 border">Prix/m² appart</th>
              <th className="p-2 border">Prix/m² + parking</th>
              <th className="p-2 border">Acquéreur(s)</th>
              <th className="p-2 border">Statut</th>
              <th className="p-2 border">Réservation</th>
              <th className="p-2 border">Acte</th>
              <th className="p-2 border">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(l => (
              <LotRow key={l.id} lot={l} onUpdate={onUpdate} variant="project" onEdit={() => setEditing(l)} clients={clients} highlight={highlightLotId === l.id} />
            ))}
            {!filtered.length && (
              <tr>
                <td className="p-4 text-center text-gray-500" colSpan={19}>Aucun lot</td>
              </tr>
            )}
          </tbody>
          {filtered.length > 0 && (
            <tfoot>
              <tr className="bg-gray-50">
                <td className="p-2 border" colSpan={11}>Total bâtiment</td>
                <td className="p-2 border font-semibold">{caTotal.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })}</td>
                <td className="p-2 border" colSpan={7}></td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      <CreateLotModal open={open} onClose={() => setOpen(false)} batimentId={batiment.id} onCreated={addLotLocal} />
      <EditLotModal open={!!editing} onClose={() => setEditing(null)} lot={editing}
        onSaved={(updated) => {
          if (!updated?.id) return
          setLots(prev => prev.map(x => x.id === updated.id ? { ...x, ...updated } : x))
          onChanged?.()
        }}
        onDeleted={(deletedId) => {
          setLots(prev => prev.filter(x => x.id !== deletedId))
          onChanged?.()
          setEditing(null)
        }}
      />
      <EditBatimentModal
        open={editBat}
        onClose={() => setEditBat(false)}
        batiment={batiment}
        onSaved={onBatimentUpdated}
      />
    </div>
  )
}
