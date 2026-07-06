import { useEffect, useState, useMemo } from 'react'
import * as XLSX from 'xlsx'
import api from '../api/axios'
import EditLotModal from '../components/EditLotModal'
import { isReadOnly } from '../utils/auth'


export default function LotsList() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Selection
  const [selectedIds, setSelectedIds] = useState(new Set())

  // Edit Modal
  const [editingLot, setEditingLot] = useState(null)

  // Filters state
  const [filters, setFilters] = useState({
    programme: 'Tous',
    type: 'Tous',
    status: 'Tous',
  })

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/lots')
      setItems(data || [])
    } catch (e) {
      console.error(e)
      setError('Impossible de charger les lots.')
    } finally {
      setLoading(false)
    }
  }

  // Compute unique values for select options
  const programmes = useMemo(() => {
    const s = new Set(items.map(i => i.programme_name).filter(Boolean))
    return Array.from(s).sort()
  }, [items])

  const types = useMemo(() => {
    const s = new Set(items.map(i => i.type).filter(Boolean))
    return Array.from(s).sort()
  }, [items])

  const statuses = ['Libre', 'Option', 'Réservé', 'Acté']

  const exportToExcel = () => {
    const exportItems = items.filter(i => selectedIds.has(i.id))
    const source = exportItems.length > 0 ? exportItems : filteredItems

    const data = source.map(item => ({
      'Programme': item.programme_name || '-',
      'Lot': item.lot,
      'Type': item.type,
      'Prix Total': item.prix_total,
      'Statut': item.statut,
      'Acquéreur': item.client_name || '-'
    }))

    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "Lots")
    XLSX.writeFile(wb, "lots_export.xlsx")
  }

  // Filter items
  const filteredItems = useMemo(() => {
    return items.filter(item => {
      const pMatch = filters.programme === 'Tous' || item.programme_name === filters.programme
      const tMatch = filters.type === 'Tous' || item.type === filters.type
      // Status loose match
      let sMatch = true
      if (filters.status !== 'Tous') {
        const itemStatus = (item.statut || 'Libre').toLowerCase()
        sMatch = itemStatus.includes(filters.status.toLowerCase()) ||
          (filters.status === 'Réservé' && (itemStatus.includes('reserv') || itemStatus === 'transit'))
      }
      return pMatch && tMatch && sMatch
    })
  }, [items, filters])

  const formatMoney = (val) =>
    (val || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

  // Selection handlers
  const toggleSelection = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (filteredItems.every(i => selectedIds.has(i.id))) {
      // Deselect all visible
      setSelectedIds(prev => {
        const next = new Set(prev)
        filteredItems.forEach(i => next.delete(i.id))
        return next
      })
    } else {
      // Select all visible
      setSelectedIds(prev => {
        const next = new Set(prev)
        filteredItems.forEach(i => next.add(i.id))
        return next
      })
    }
  }

  const handleSaved = (savedLot) => {
    setItems(prev => prev.map(i => i.id === savedLot.id ? { ...i, ...savedLot } : i))
    load() // Reload to catch any server-side effect or association details if needed
  }

  if (loading) return <div className="p-6">Chargement...</div>

  return (
    <div className="w-full px-4 py-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-2xl font-bold text-gray-800">Grille des Lots</h1>

        <div className="flex gap-4 items-center">
          <button
            onClick={exportToExcel}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium flex items-center gap-2"
          >
            <span>Export Excel ({selectedIds.size > 0 ? selectedIds.size : 'Tous'})</span>
          </button>

          {/* Filter Bar */}
          <div className="flex flex-wrap gap-2 items-center bg-white p-2 rounded shadow-sm border">
            <select
              className="p-2 border rounded text-sm min-w-[150px]"
              value={filters.programme}
              onChange={e => setFilters(prev => ({ ...prev, programme: e.target.value }))}
            >
              <option value="Tous">Tous les programmes</option>
              {programmes.map(p => <option key={p} value={p}>{p}</option>)}
            </select>

            <select
              className="p-2 border rounded text-sm min-w-[100px]"
              value={filters.type}
              onChange={e => setFilters(prev => ({ ...prev, type: e.target.value }))}
            >
              <option value="Tous">Tous types</option>
              {types.map(t => <option key={t} value={t}>{t}</option>)}
            </select>

            <select
              className="p-2 border rounded text-sm min-w-[100px]"
              value={filters.status}
              onChange={e => setFilters(prev => ({ ...prev, status: e.target.value }))}
            >
              <option value="Tous">Tous statuts</option>
              {statuses.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      {error && <div className="p-4 bg-red-50 text-red-600 rounded mb-4 border border-red-200">{error}</div>}

      <div className="overflow-x-auto bg-white border rounded shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 text-gray-700 uppercase leading-normal text-xs tracking-wider">
            <tr>
              <th className="p-3 w-10 text-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={filteredItems.length > 0 && filteredItems.every(i => selectedIds.has(i.id))}
                  onChange={toggleAll}
                />
              </th>
              <th className="p-3 text-left font-semibold">Programme</th>
              <th className="p-3 text-left font-semibold">Lot</th>
              <th className="p-3 text-left font-semibold">Type</th>
              <th className="p-3 text-left font-semibold">Prix Logement</th>
              <th className="p-3 text-left font-semibold">Prix Stat.</th>
              <th className="p-3 text-left font-semibold">Prix Total</th>
              <th className="p-3 text-left font-semibold">Statut</th>
              <th className="p-3 text-left font-semibold">Acquéreur</th>
              <th className="p-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="text-gray-600 whitespace-nowrap">
            {filteredItems.map(lot => (
              <tr key={lot.id} className={`hover:bg-blue-50 transition-colors ${selectedIds.has(lot.id) ? 'bg-blue-50' : ''} border-b border-gray-100`}>
                <td className="p-3 text-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={selectedIds.has(lot.id)}
                    onChange={() => toggleSelection(lot.id)}
                  />
                </td>
                <td className="p-3 text-sm">{lot.programme_name || '-'}</td>
                <td className="p-3 text-sm font-medium text-gray-900">{lot.lot}</td>
                <td className="p-3 text-sm">{lot.type}</td>
                <td className="p-3 text-sm text-gray-500">{formatMoney(lot.prix_logement)}</td>
                <td className="p-3 text-sm text-gray-500">{formatMoney(lot.prix_stationnement)}</td>
                <td className="p-3 text-sm font-medium text-blue-900">{formatMoney(lot.prix_total)}</td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold
                    ${(() => {
                      const lower = (lot.statut || '').toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                      if (lower.includes('option')) return 'bg-green-100 text-green-800'
                      if (lower.includes('reserv')) return 'bg-red-100 text-red-800'
                      if (lower.includes('acte')) return 'bg-blue-100 text-blue-800'
                      return 'bg-gray-100 text-gray-800'
                    })()}
                  `}>
                    {lot.statut || 'Libre'}
                  </span>
                </td>
                <td className="p-3 text-sm">
                  {lot.client_name ? (
                    <span className="font-medium text-blue-900">{lot.client_name}</span>
                  ) : (
                    <span className="text-gray-400 italic text-xs">Aucun</span>
                  )}
                </td>
                <td className="p-3 text-right">
                  {!isReadOnly() && (
                    <button
                      onClick={() => setEditingLot(lot)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors shadow-sm"
                    >
                      Modifier
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {filteredItems.length === 0 && (
              <tr>
                <td colSpan="10" className="p-8 text-center text-gray-500">
                  Aucun lot ne correspond aux filtres.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-2 text-xs text-gray-400 flex justify-between">
        <span>{selectedIds.size} lots sélectionnés</span>
        <span>Total {filteredItems.length} lots affichés</span>
      </div>

      <EditLotModal
        open={!!editingLot}
        onClose={() => setEditingLot(null)}
        lot={editingLot}
        onSaved={handleSaved}
      />
    </div>
  )
}
