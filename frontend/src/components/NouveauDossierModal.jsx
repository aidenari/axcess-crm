import { useEffect, useState } from 'react'
import api from '../api/axios'

const EMPTY_PERSONNE = {
  civility: '',
  last_name: '',
  first_name: '',
  email: '',
  phone: '',
  address: '',
  address2: '',
  origin: '',
}

function CpHelper({ form, setForm }) {
  const [cp, setCp] = useState('')
  const [cities, setCities] = useState([])

  useEffect(() => {
    if (cp.length === 5) {
      fetch(`https://geo.api.gouv.fr/communes?codePostal=${cp}&fields=nom,code&format=json`)
        .then(r => r.json())
        .then(data => {
          setCities(data || [])
          if (data?.length === 1) {
            const city = data[0].nom
            setForm(prev => ({ ...prev, address: `${cp} ${city} ` }))
          }
        })
        .catch(() => {})
    } else {
      setCities([])
    }
  }, [cp])

  return (
    <div className="col-span-2 border rounded p-2 bg-gray-50 text-xs">
      <div className="font-semibold text-gray-500 mb-1">Aide saisie adresse</div>
      <div className="flex gap-2 items-center flex-wrap">
        <input
          className="input text-xs px-2 py-1 w-24"
          placeholder="Code postal"
          maxLength={5}
          value={cp}
          onChange={e => setCp(e.target.value)}
        />
        {cities.map(c => (
          <button
            key={c.code}
            type="button"
            className="bg-blue-100 px-2 py-0.5 rounded hover:bg-blue-200 text-xs"
            onClick={() => { setForm(prev => ({ ...prev, address: `${cp} ${c.nom} ` })); setCities([]) }}
          >
            {c.nom}
          </button>
        ))}
      </div>
    </div>
  )
}

function PersonneForm({ title, form, setForm }) {
  const onChange = e => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))

  return (
    <div className="grid grid-cols-2 gap-2">
      {title && <div className="col-span-2 font-semibold text-sm text-gray-700 border-b pb-1">{title}</div>}
      <div className="col-span-2 flex gap-4 text-sm">
        {['M.', 'Mme'].map(v => (
          <label key={v} className="flex items-center gap-1 cursor-pointer">
            <input type="radio" name="civility" value={v} checked={form.civility === v} onChange={onChange} />
            {v}
          </label>
        ))}
      </div>
      <input className="input text-sm" name="last_name" placeholder="Nom *" value={form.last_name} onChange={onChange} required />
      <input className="input text-sm" name="first_name" placeholder="Prénom *" value={form.first_name} onChange={onChange} required />
      <input className="input text-sm" name="email" type="email" placeholder="Email" value={form.email} onChange={onChange} />
      <input className="input text-sm" name="phone" placeholder="Téléphone" value={form.phone} onChange={onChange} />
      <CpHelper form={form} setForm={setForm} />
      <input className="input text-sm col-span-2" name="address" placeholder="Adresse" value={form.address} onChange={onChange} />
      <input className="input text-sm col-span-2" name="address2" placeholder="Adresse 2 (facultatif)" value={form.address2} onChange={onChange} />
      <input className="input text-sm col-span-2" name="origin" placeholder="Origine du contact" value={form.origin} onChange={onChange} />
    </div>
  )
}

export default function NouveauDossierModal({ open, onClose, onCreated, programmes }) {
  const [step, setStep] = useState(1)
  const [type, setType] = useState(null) // "solo" | "couple"
  const [p1, setP1] = useState({ ...EMPTY_PERSONNE })
  const [p2, setP2] = useState({ ...EMPTY_PERSONNE })
  const [programmeId, setProgrammeId] = useState('')
  const [lotId, setLotId] = useState('')
  const [lots, setLots] = useState([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) {
      setStep(1); setType(null)
      setP1({ ...EMPTY_PERSONNE }); setP2({ ...EMPTY_PERSONNE })
      setProgrammeId(''); setLotId(''); setLots([])
      setError('')
    }
  }, [open])

  useEffect(() => {
    if (!programmeId) { setLots([]); setLotId(''); return }
    api.get('/lots', { params: { programme_id: programmeId } })
      .then(r => setLots(r.data || []))
      .catch(() => setLots([]))
  }, [programmeId])

  const chooseType = (t) => { setType(t); setStep(2) }

  const goStep3 = (e) => {
    e.preventDefault()
    if (!p1.last_name.trim() || !p1.first_name.trim()) {
      setError('Nom et prénom de la personne 1 sont obligatoires.')
      return
    }
    if (type === 'couple' && (!p2.last_name.trim() || !p2.first_name.trim())) {
      setError('Nom et prénom de la personne 2 sont obligatoires.')
      return
    }
    setError('')
    setStep(3)
  }

  const save = async () => {
    if (!programmeId) { setError('Veuillez sélectionner un programme.'); return }
    setSaving(true)
    setError('')
    try {
      const payload = {
        type,
        programme_id: Number(programmeId),
        lot_id: lotId ? Number(lotId) : null,
        personne1: p1,
        personne2: type === 'couple' ? p2 : undefined,
      }
      await api.post('/dossiers', payload)
      onCreated?.()
      onClose()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Erreur lors de la création du dossier.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">Nouveau dossier acquéreur</h2>
            <div className="flex gap-2 mt-1">
              {[1, 2, 3].map(n => (
                <span
                  key={n}
                  className={`text-xs px-2 py-0.5 rounded-full ${step === n ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500'}`}
                >
                  Étape {n}
                </span>
              ))}
            </div>
          </div>
          <button type="button" className="text-gray-400 hover:text-gray-600 text-2xl leading-none" onClick={onClose}>×</button>
        </div>

        <div className="px-6 py-5">
          {/* Step 1 — Solo ou Couple */}
          {step === 1 && (
            <div>
              <p className="text-sm text-gray-600 mb-6">Ce dossier concerne :</p>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { key: 'solo', label: 'Solo', desc: '1 acquéreur', icon: '👤' },
                  { key: 'couple', label: 'Couple', desc: '2 acquéreurs', icon: '👥' },
                ].map(opt => (
                  <button
                    key={opt.key}
                    type="button"
                    onClick={() => chooseType(opt.key)}
                    className="border-2 rounded-xl p-8 text-center hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <div className="text-4xl mb-2">{opt.icon}</div>
                    <div className="text-xl font-semibold">{opt.label}</div>
                    <div className="text-sm text-gray-500 mt-1">{opt.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Step 2 — Formulaire personne(s) */}
          {step === 2 && (
            <form onSubmit={goStep3}>
              {error && <div className="text-red-600 text-sm mb-3">{error}</div>}
              {type === 'solo' ? (
                <PersonneForm title={null} form={p1} setForm={setP1} />
              ) : (
                <div className="grid grid-cols-2 gap-6">
                  <PersonneForm title="Personne 1" form={p1} setForm={setP1} />
                  <PersonneForm title="Personne 2" form={p2} setForm={setP2} />
                </div>
              )}
              <div className="flex justify-between mt-6">
                <button type="button" className="btn" onClick={() => setStep(1)}>← Retour</button>
                <button type="submit" className="btn bg-blue-600 hover:bg-blue-700 text-white">
                  Suivant : associer un lot →
                </button>
              </div>
            </form>
          )}

          {/* Step 3 — Lot (optionnel) */}
          {step === 3 && (
            <div>
              {error && <div className="text-red-600 text-sm mb-3">{error}</div>}
              <p className="text-sm text-gray-600 mb-4">
                Associer ce dossier à un lot (optionnel — peut être fait plus tard).
              </p>
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Programme *</label>
                  <select
                    className="input"
                    value={programmeId}
                    onChange={e => setProgrammeId(e.target.value)}
                  >
                    <option value="">Sélectionner un programme</option>
                    {programmes.map(p => (
                      <option key={p.id} value={p.id}>{p.nom}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1">Lot (facultatif)</label>
                  <select
                    className="input"
                    value={lotId}
                    onChange={e => setLotId(e.target.value)}
                    disabled={!programmeId}
                  >
                    <option value="">Aucun lot</option>
                    {lots
                      .filter(l => !l.dossier_id)
                      .map(l => (
                        <option key={l.id} value={l.id}>{l.lot || `Lot #${l.id}`}</option>
                      ))}
                  </select>
                  {programmeId && lots.filter(l => l.dossier_id).length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">Les lots déjà assignés sont masqués.</p>
                  )}
                </div>
              </div>

              <div className="border rounded-lg p-4 bg-gray-50 mb-6 text-sm">
                <div className="font-medium text-gray-700 mb-2">Récapitulatif</div>
                <div><span className="text-gray-500">Type :</span> {type === 'solo' ? 'Solo' : 'Couple'}</div>
                <div><span className="text-gray-500">Personne 1 :</span> {p1.last_name} {p1.first_name}</div>
                {type === 'couple' && (
                  <div><span className="text-gray-500">Personne 2 :</span> {p2.last_name} {p2.first_name}</div>
                )}
              </div>

              <div className="flex justify-between">
                <button type="button" className="btn" onClick={() => setStep(2)}>← Retour</button>
                <button
                  type="button"
                  className="btn bg-green-600 hover:bg-green-700 text-white"
                  onClick={save}
                  disabled={saving || !programmeId}
                >
                  {saving ? 'Enregistrement...' : 'Créer le dossier'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
