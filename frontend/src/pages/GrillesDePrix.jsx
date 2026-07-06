import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import api from '../api/axios'
import ProgrammeHeader from '../components/ProgrammeHeader.jsx'
import StatsBar from '../components/StatsBar.jsx'
import BatimentCard from '../components/BatimentCard.jsx'
import CreateBatimentModal from '../components/CreateBatimentModal.jsx'
import { isReadOnly } from '../utils/auth'

export default function GrillesDePrix() {
  const { programme_id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [programmes, setProgrammes] = useState([])
  const [selectedProgramme, setSelectedProgramme] = useState(() => {
    if (programme_id) return String(programme_id)
    const saved = localStorage.getItem('last_selected_programme')
    return saved !== null ? saved : null
  })
  const [programme, setProgramme] = useState(null)
  const [stats, setStats] = useState(null)
  const [batiments, setBatiments] = useState([])
  const [filters, setFilters] = useState({ statut: 'Tous', type: 'Tous', batiment: 'Tous' })
  const [openBatModal, setOpenBatModal] = useState(false)
  const [highlightLotId, setHighlightLotId] = useState(null)
  const [showImportWarning, setShowImportWarning] = useState(false)
  const [importReport, setImportReport] = useState(null)
  const fileRef = useRef(null)

  useEffect(() => {
    if (selectedProgramme !== null) {
      localStorage.setItem('last_selected_programme', selectedProgramme)
    }
  }, [selectedProgramme])

  const loadProgrammesList = async () => {
    try {
      const { data } = await api.get('/programmes')
      setProgrammes(data || [])

      const currentId = selectedProgramme

      // If provided via URL, always prioritize (already handled in initial state, 
      // but if URL changes it's handled by another useEffect)

      if ((data?.length || 0) > 0) {
        if (currentId === null) {
          // No history, default to first
          setSelectedProgramme(String(data[0].id))
        } else if (currentId) {
          // Verify existence
          const exists = data.find(p => String(p.id) === String(currentId))
          if (!exists) {
            // Was selected but deleted? Default to first or empty?
            // Let's default to first to be safe, or empty.
            // If we fallback to empty, user sees nothing.
            // Let's fallback to first as that's safe behavior for "invalid ID".
            setSelectedProgramme(String(data[0].id))
          }
        }
        // If currentId === "", user specifically wanted empty, so we do nothing (keep it empty)
      }
    } catch (e) { console.error(e) }
  }

  const loadProgramme = async () => {
    try {
      if (!selectedProgramme) { setProgramme(null); return }
      const { data } = await api.get(`/programmes/${selectedProgramme}`)
      setProgramme(data)
    } catch (e) { console.error(e) }
  }
  const loadStats = async () => {
    try {
      if (!selectedProgramme) { setStats(null); return }
      const { data } = await api.get(`/programmes/${selectedProgramme}/statistics`)
      setStats(data)
    } catch (e) { console.error(e) }
  }
  const loadBatiments = async () => {
    try {
      if (!selectedProgramme) { setBatiments([]); return }
      const { data } = await api.get('/batiments', { params: { programme_id: selectedProgramme } })
      setBatiments(data || [])
    } catch (e) { console.error(e) }
  }

  useEffect(() => { loadProgrammesList() }, [])
  useEffect(() => { if (programme_id) setSelectedProgramme(String(programme_id)) }, [programme_id])
  useEffect(() => {
    if (!selectedProgramme) return
    loadProgramme(); loadStats(); loadBatiments()
  }, [selectedProgramme])

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const raw = params.get('highlight_lot')
    if (!raw) {
      setHighlightLotId(null)
      return
    }
    const id = Number(raw)
    if (!Number.isFinite(id)) {
      setHighlightLotId(null)
      return
    }
    setHighlightLotId(id)
    const timer = setTimeout(() => setHighlightLotId(null), 4000)
    return () => clearTimeout(timer)
  }, [location.search])

  const onCreatedBatiment = (bat) => {
    setBatiments(prev => [bat, ...prev])
  }

  const exportCSV = async () => {
    if (!selectedProgramme) return
    try {
      const res = await api.get('/lots/export', { params: { programme_id: selectedProgramme }, responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `lots_programme_${selectedProgramme}.csv`
      a.click(); URL.revokeObjectURL(url)
    } catch (e) { console.error(e) }
  }

  const downloadTemplate = async () => {
    try {
      const res = await api.get('/lots/csv-template', { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'modele_grille_prix.csv'
      a.click(); URL.revokeObjectURL(url)
    } catch (e) { console.error(e) }
  }

  const onImport = async (file) => {
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    try {
      const { data } = await api.post(`/lots/import?programme_id=${selectedProgramme}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setImportReport(data)
      loadStats(); loadBatiments()
    } catch (e) { console.error(e) }
    // reset file input so the same file can be re-imported
    if (fileRef.current) fileRef.current.value = ''
  }

  /* Sort buildings alphabetically */
  const sortedBatiments = useMemo(() => {
    return [...batiments].sort((a, b) => {
      const nA = a.nom || a.name || ''
      const nB = b.nom || b.name || ''
      return nA.localeCompare(nB)
    })
  }, [batiments])

  const options = useMemo(() => {
    const batNames = sortedBatiments.map(b => b.nom || b.name).filter(Boolean)
    return { batiments: batNames }
  }, [sortedBatiments])

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <button className="text-blue-700 hover:underline" onClick={() => navigate('/programmes')}>← Tous les projets</button>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Programme</label>
          <select className="input" value={selectedProgramme} onChange={(e) => setSelectedProgramme(e.target.value)}>
            <option value="">Sélectionner</option>
            {programmes.map(p => (
              <option key={p.id} value={p.id}>{p.nom || p.name}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex items-center justify-end mb-4">
        <div className="flex items-center gap-2">
          <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700" onClick={exportCSV}>Exporter CSV</button>
          {!isReadOnly() && (
            <>
              <button className="px-4 py-2 rounded border text-sm text-gray-600 hover:bg-gray-50" onClick={downloadTemplate}>⬇ Modèle CSV</button>
              <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => onImport(e.target.files?.[0])} />
              <button className="px-4 py-2 rounded border" onClick={() => setShowImportWarning(true)}>Importer CSV</button>
              <button className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700" onClick={() => setOpenBatModal(true)}>+ Bâtiment</button>
            </>
          )}
        </div>
      </div>

      {/* Import warning modal */}
      {showImportWarning && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4">
            <h2 className="text-lg font-semibold mb-3">⚠️ Format d'import requis</h2>
            <p className="text-sm text-gray-700 mb-3">
              Avant d'importer, assurez-vous que votre fichier CSV respecte exactement ce format :
            </p>
            <div className="bg-gray-50 rounded p-3 text-xs font-mono mb-3 overflow-x-auto">
              batiment_nom | lot | niveau | type | surface_sol | sha_m2 | orientation | garage | parking1 | parking2 | cave | jardin | terrasse | prix_logement | prix_stationnement | prix_total | prix_m2_appartement | prix_m2_appart_parking | acquereur | statut
            </div>
            <ul className="text-sm text-gray-700 space-y-1 mb-4 list-disc list-inside">
              <li>La première ligne doit être l'en-tête (noms des colonnes)</li>
              <li><strong>batiment_nom</strong> : nom exact du bâtiment (ex: Bâtiment A) — sera créé s'il n'existe pas</li>
              <li><strong>garage, parking1, parking2, cave</strong> : <code>Oui</code> ou <code>Non</code></li>
              <li><strong>statut</strong> : Libre, Réservé, Option ou Acté</li>
              <li><strong>Prix</strong> : nombre entier ou décimal (ex: 250000 ou 250000.00)</li>
              <li><strong>acquereur</strong> : laisser vide si aucun</li>
            </ul>
            <p className="text-xs text-blue-700 mb-4">💡 Conseil : exportez d'abord une grille existante pour obtenir un fichier au bon format.</p>
            <div className="flex justify-end gap-2">
              <button className="px-4 py-2 rounded border text-gray-600 hover:bg-gray-50" onClick={() => setShowImportWarning(false)}>Annuler</button>
              <button className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700" onClick={() => { setShowImportWarning(false); fileRef.current?.click() }}>J'ai compris, choisir un fichier</button>
            </div>
          </div>
        </div>
      )}

      {/* Import report modal */}
      {importReport && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-lg font-semibold mb-4">Résultat de l'import</h2>
            <p className="text-sm mb-1">✅ <strong>{importReport.created}</strong> lot{importReport.created !== 1 ? 's' : ''} créé{importReport.created !== 1 ? 's' : ''}</p>
            <p className="text-sm mb-3">🔄 <strong>{importReport.updated}</strong> lot{importReport.updated !== 1 ? 's' : ''} mis à jour</p>
            {importReport.errors?.length > 0 && (
              <div className="mb-3">
                <p className="text-sm font-medium text-amber-700 mb-1">⚠️ {importReport.errors.length} ligne{importReport.errors.length !== 1 ? 's' : ''} ignorée{importReport.errors.length !== 1 ? 's' : ''} :</p>
                <ul className="text-xs text-gray-600 space-y-1 max-h-40 overflow-y-auto bg-amber-50 rounded p-2">
                  {importReport.errors.map((err, i) => (
                    <li key={i}>Ligne {err.ligne} : {err.raison}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex justify-end">
              <button className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700" onClick={() => setImportReport(null)}>Fermer</button>
            </div>
          </div>
        </div>
      )}

      {programme && (
        <div className="mb-4">
          <h2 className="text-2xl font-semibold mb-3">{programme.nom || programme.name}</h2>
          <ProgrammeHeader programme={programme} />
        </div>
      )}

      {stats && (
        <div className="mb-4">
          <StatsBar stats={stats} />
        </div>
      )}

      <div className="flex items-center justify-between mb-3">
        <div className="flex flex-wrap gap-3">
          <div>
            <label className="text-sm text-gray-600 mr-2">Bâtiment</label>
            <select className="input" value={filters.batiment} onChange={(e) => setFilters(f => ({ ...f, batiment: e.target.value }))}>
              <option value="Tous">Tous</option>
              {options.batiments.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 mr-2">Statut</label>
            <select className="input" value={filters.statut} onChange={(e) => setFilters(f => ({ ...f, statut: e.target.value }))}>
              {['Tous', 'Libre', 'Option', 'Réservation', 'Acté'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 mr-2">Type</label>
            <select className="input" value={filters.type} onChange={(e) => setFilters(f => ({ ...f, type: e.target.value }))}>
              {['Tous', 'T1', 'T2', 'T3', 'T4', 'T5'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {sortedBatiments
          .filter(b => filters.batiment === 'Tous' || (b.nom || b.name) === filters.batiment)
          .map(b => (
            <BatimentCard
              key={b.id}
              batiment={b}
              filters={filters}
              onLotsChanged={loadStats}
              onAddBatimentClick={() => setOpenBatModal(true)}
              highlightLotId={highlightLotId}
              onBatimentUpdated={(updated) => {
                setBatiments(prev => prev.map(x => x.id === updated.id ? updated : x))
              }}
              onBatimentDeleted={(id) => {
                setBatiments(prev => prev.filter(x => x.id !== id))
              }}
            />
          ))}
        {!batiments.length && (
          <div className="text-gray-500 text-sm">Aucun bâtiment pour ce programme.</div>
        )}
      </div>

      <CreateBatimentModal open={openBatModal} onClose={() => setOpenBatModal(false)} programmeId={selectedProgramme} onCreated={onCreatedBatiment} />
    </div>
  )
}
