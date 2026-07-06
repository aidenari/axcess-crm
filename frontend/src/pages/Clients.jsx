import { useEffect, useState } from 'react'
import api from '../api/axios'
import { isReadOnly } from '../utils/auth'
import { formatPhone } from '../utils/formatPhone'
import ClientDrawer from '../components/ClientDrawer'

// ---- Modale de confirmation ----
function ConfirmModal({ open, title, message, onCancel, onConfirm }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onCancel}>
      <div className="bg-white rounded-lg w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-sm text-gray-600 mb-4">{message}</p>
        <div className="flex justify-end gap-2">
          <button className="btn" type="button" onClick={onCancel}>Annuler</button>
          <button className="btn bg-red-600 hover:bg-red-700 text-white" type="button" onClick={onConfirm}>
            Confirmer
          </button>
        </div>
      </div>
    </div>
  )
}

// ---- Page principale ----
export default function Clients() {
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(false)
  const [filterType, setFilterType] = useState('all') // 'all' | 'prospect' | 'acquereur'
  const [searchNom, setSearchNom] = useState('')
  const [showDrawer, setShowDrawer] = useState(false)
  const [editingClient, setEditingClient] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/clients')
      setClients(data || [])
    } catch {
      setClients([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const nomsOf = (c) => {
    const n1 = `${c.last_name || ''} ${c.first_name || ''}`.trim()
    if (c.partner) {
      const n2 = `${c.partner.last_name || ''} ${c.partner.first_name || ''}`.trim()
      return n2 ? `${n1} + ${n2}` : n1
    }
    return n1
  }

  const emailsOf = (c) => [c.email, c.partner?.email].filter(Boolean).join(', ')
  const phonesOf = (c) => [c.phone, c.partner?.phone].filter(Boolean).map(formatPhone).join(', ')

  const filtered = clients.filter(c => {
    const matchType = filterType === 'all' || c.type === filterType
    const matchNom = !searchNom || nomsOf(c).toLowerCase().includes(searchNom.toLowerCase())
    return matchType && matchNom
  })

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await api.delete(`/clients/${deleteTarget.id}`)
      setDeleteTarget(null)
      load()
    } catch {
      alert('Erreur lors de la suppression du client.')
    }
  }

  return (
    <div>
      {/* En-tête */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Clients</h1>
        {!isReadOnly() && (
          <button
            className="btn bg-blue-600 hover:bg-blue-700 text-white"
            type="button"
            onClick={() => { setEditingClient(null); setShowDrawer(true) }}
          >
            + Nouveau client
          </button>
        )}
      </div>

      {/* Filtres */}
      <div className="card mb-4">
        <div className="grid grid-cols-4 gap-3">
          <input
            className="input col-span-2"
            placeholder="Rechercher par nom"
            value={searchNom}
            onChange={e => setSearchNom(e.target.value)}
          />
          <select className="input col-span-2" value={filterType} onChange={e => setFilterType(e.target.value)}>
            <option value="all">Tous les types</option>
            <option value="prospect">Prospect</option>
            <option value="acquereur">Acquéreur</option>
          </select>
        </div>
        {(searchNom || filterType !== 'all') && (
          <div className="flex justify-end mt-2">
            <button
              className="text-xs text-gray-500 hover:text-gray-800 underline"
              type="button"
              onClick={() => { setSearchNom(''); setFilterType('all') }}
            >
              Réinitialiser les filtres
            </button>
          </div>
        )}
      </div>

      {/* Tableau */}
      {loading && <div className="p-4 text-sm text-gray-500">Chargement...</div>}
      {!loading && filtered.length === 0 && (
        <div className="p-4 text-sm text-gray-500">Aucun client trouvé.</div>
      )}
      {!loading && filtered.length > 0 && (
        <div className="overflow-x-auto rounded border">
          <table className="w-full text-xs bg-white">
            <thead className="bg-gray-50 text-gray-600">
              <tr className="text-left">
                <th className="px-3 py-2 border-b font-medium">Nom(s)</th>
                <th className="px-3 py-2 border-b font-medium">Email(s)</th>
                <th className="px-3 py-2 border-b font-medium">Téléphone(s)</th>
                <th className="px-3 py-2 border-b font-medium">Type</th>
                <th className="px-3 py-2 border-b font-medium">Programme / Lot</th>
                <th className="px-3 py-2 border-b font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="hover:bg-gray-50 border-b last:border-b-0">
                  <td className="px-3 py-2 font-medium whitespace-nowrap">{nomsOf(c) || '—'}</td>
                  <td className="px-3 py-2 max-w-[200px] truncate" title={emailsOf(c)}>{emailsOf(c) || '—'}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{phonesOf(c) || '—'}</td>
                  <td className="px-3 py-2">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${c.type === 'acquereur' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                      {c.type === 'acquereur' ? 'Acquéreur' : 'Prospect'}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {c.programme_name
                      ? `${c.programme_name}${c.lot_label ? ' / ' + c.lot_label : ''}`
                      : <span className="text-gray-400 italic">—</span>
                    }
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    {!isReadOnly() && (
                      <div className="flex gap-2">
                        <button
                          className="text-blue-600 hover:underline text-xs"
                          type="button"
                          onClick={() => { setEditingClient(c); setShowDrawer(true) }}
                        >
                          Modifier
                        </button>
                        <button
                          className="text-red-500 hover:underline text-xs"
                          type="button"
                          onClick={() => setDeleteTarget(c)}
                        >
                          Supprimer
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Compteur */}
      {!loading && filtered.length > 0 && (
        <div className="text-xs text-gray-400 mt-2 text-right">
          {filtered.length} client{filtered.length > 1 ? 's' : ''}
        </div>
      )}

      {/* Drawer création / modification */}
      <ClientDrawer
        open={showDrawer}
        onClose={() => { setShowDrawer(false); setEditingClient(null) }}
        onSaved={() => { load() }}
        editingClient={editingClient}
      />

      {/* Confirmation suppression */}
      <ConfirmModal
        open={Boolean(deleteTarget)}
        title="Supprimer le client"
        message={`Supprimer le client ${deleteTarget ? nomsOf(deleteTarget) : ''} ?`}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
      />
    </div>
  )
}
