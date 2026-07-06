import { useEffect, useState } from 'react'
import api from '../api/axios'

function Drawer({ open, onClose, title, children }) {
    if (!open) return null
    return (
        <div className="fixed inset-0 z-[60] bg-black/40" onClick={onClose}>
            <div className="absolute inset-y-0 right-0 w-full max-w-2xl bg-white p-6 shadow-xl flex flex-col" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold">{title}</h2>
                    <button className="btn" type="button" onClick={onClose}>Fermer</button>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {children}
                </div>
            </div>
        </div>
    )
}

const emptyPartner = {
    civility: '', last_name: '', first_name: '', email: '', phone: '',
}

export default function ClientDrawer({ open, onClose, onSaved, editingClient = null }) {
    const [loading, setLoading] = useState(false)
    const [programmes, setProgrammes] = useState([])
    const [drawerLots, setDrawerLots] = useState([])
    const isEditing = Boolean(editingClient)

    // Form State
    const [form, setForm] = useState({
        civility: '',
        type: 'prospect',
        last_name: '',
        first_name: '',
        address: '',
        address2: '',
        phone: '',
        phone2: '',
        email: '',
        email2: '',
        origin: '',
        programme_id: '',
        lot_id: '',
    })

    const [hasPartner, setHasPartner] = useState(false)
    const [partner, setPartner] = useState(emptyPartner)

    // Address Helper State
    const [cp, setCp] = useState('')
    const [cities, setCities] = useState([])

    useEffect(() => {
        if (open) {
            if (editingClient) {
                setForm({
                    civility: editingClient.civility || '',
                    type: editingClient.type || 'prospect',
                    last_name: editingClient.last_name || '',
                    first_name: editingClient.first_name || '',
                    address: editingClient.address || '',
                    address2: editingClient.address2 || '',
                    phone: editingClient.phone || '',
                    phone2: editingClient.phone2 || '',
                    email: editingClient.email || '',
                    email2: editingClient.email2 || '',
                    origin: editingClient.origin || '',
                    programme_id: editingClient.programme_id ? String(editingClient.programme_id) : '',
                    lot_id: editingClient.lot_id ? String(editingClient.lot_id) : '',
                })
                if (editingClient.partner) {
                    setHasPartner(true)
                    setPartner({
                        civility: editingClient.partner.civility || '',
                        last_name: editingClient.partner.last_name || '',
                        first_name: editingClient.partner.first_name || '',
                        email: editingClient.partner.email || '',
                        phone: editingClient.partner.phone || '',
                    })
                } else {
                    setHasPartner(false)
                    setPartner(emptyPartner)
                }
                if (editingClient.programme_id) {
                    api.get('/lots', { params: { programme_id: editingClient.programme_id } })
                        .then(({ data }) => setDrawerLots(data || []))
                        .catch(() => setDrawerLots([]))
                } else {
                    setDrawerLots([])
                }
            } else {
                // Reset form on open
                setForm({
                    civility: '', type: 'prospect', last_name: '', first_name: '',
                    address: '', address2: '', phone: '', phone2: '', email: '', email2: '',
                    origin: '', programme_id: '', lot_id: ''
                })
                setHasPartner(false)
                setPartner(emptyPartner)
            }
            setCp('')
            setCities([])
            loadProgrammes()
        }
    }, [open, editingClient])

    const loadProgrammes = async () => {
        try {
            const { data } = await api.get('/programmes')
            setProgrammes(data || [])
        } catch {
            setProgrammes([])
        }
    }

    const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })
    const onPartnerChange = (e) => setPartner({ ...partner, [e.target.name]: e.target.value })

    // Address Lookup Logic
    useEffect(() => {
        if (cp.length === 5) {
            fetch(`https://geo.api.gouv.fr/communes?codePostal=${cp}&fields=nom,code,codesPostaux&format=json&geometry=centre`)
                .then(r => r.json())
                .then(data => {
                    setCities(data || [])
                    if (data && data.length === 1) {
                        const city = data[0].nom
                        if (!form.address.includes(city)) {
                            setForm(prev => ({ ...prev, address: `${prev.address ? prev.address + ' ' : ''}${cp} ${city}` }))
                        }
                    }
                })
                .catch(console.error)
        } else {
            setCities([])
        }
    }, [cp])

    const onSelectCity = (city) => {
        setForm(prev => ({ ...prev, address: `${cp} ${city} ` }))
        setCities([])
    }

    const onDrawerProgrammeChange = async (value) => {
        setForm((prev) => ({ ...prev, programme_id: value, lot_id: '' }))
        if (!value) {
            setDrawerLots([])
            return
        }
        try {
            const { data } = await api.get('/lots', { params: { programme_id: value } })
            setDrawerLots(data || [])
        } catch {
            setDrawerLots([])
        }
    }

    const saveClient = async (e) => {
        e.preventDefault()
        if (!form.last_name.trim() || !form.first_name.trim() || !form.type) {
            alert('Nom, prenom et type sont obligatoires')
            return
        }
        setLoading(true)
        const payload = {
            civility: form.civility || null,
            type: form.type,
            last_name: form.last_name,
            first_name: form.first_name,
            address: form.address || null,
            address2: form.address2 || null,
            phone: form.phone || null,
            phone2: form.phone2 || null,
            email: form.email || null,
            email2: form.email2 || null,
            origin: form.origin || null
        }
        if (!isEditing && hasPartner && (partner.last_name.trim() || partner.first_name.trim())) {
            payload.partner = {
                civility: partner.civility || null,
                type: form.type,
                last_name: partner.last_name,
                first_name: partner.first_name,
                email: partner.email || null,
                phone: partner.phone || null,
            }
        }
        try {
            let client
            if (isEditing) {
                const { data } = await api.put(`/clients/${editingClient.id}`, payload)
                client = data
            } else {
                const { data } = await api.post('/clients', payload)
                client = data
            }

            // Associate Lot if selected
            if (form.lot_id) {
                await api.put(`/lots/${form.lot_id}`, { client_id: client.id })
            }

            onSaved?.(client)
            onClose()
        } catch (e) {
            console.error(e)
            alert(isEditing ? 'Erreur modification client' : 'Erreur creation client')
        } finally {
            setLoading(false)
        }
    }

    return (
        <Drawer open={open} onClose={onClose} title={isEditing ? 'Modifier le client' : 'Créer un client'}>
            <form onSubmit={saveClient} className="grid grid-cols-4 gap-3 p-1">
                <div className="col-span-4">
                    <div className="text-sm font-medium mb-2">Civilité</div>
                    <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input type="radio" name="civility" value="M." checked={form.civility === 'M.'} onChange={onChange} />
                            M.
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input type="radio" name="civility" value="Mme" checked={form.civility === 'Mme'} onChange={onChange} />
                            Mme
                        </label>
                    </div>
                </div>
                <input className="input col-span-2" name="last_name" placeholder="Nom" value={form.last_name} onChange={onChange} required />
                <input className="input col-span-2" name="first_name" placeholder="Prénom" value={form.first_name} onChange={onChange} required />
                <input className="input col-span-2" name="email" type="email" placeholder="Email" value={form.email} onChange={onChange} />
                <input className="input col-span-2" name="email2" type="email" placeholder="Email 2 (Facultatif)" value={form.email2} onChange={onChange} />

                <input className="input col-span-2" name="phone" placeholder="Téléphone" value={form.phone} onChange={onChange} />
                <input className="input col-span-2" name="phone2" placeholder="Téléphone 2 (Facultatif)" value={form.phone2} onChange={onChange} />

                <div className="col-span-4 grid grid-cols-4 gap-2 border p-2 rounded bg-gray-50 mb-2">
                    <span className="col-span-4 text-xs font-semibold text-gray-500">Aide Saisie Adresse</span>
                    <input
                        className="input col-span-1"
                        placeholder="Code Postal"
                        value={cp}
                        onChange={e => setCp(e.target.value)}
                        maxLength={5}
                    />
                    {cities.length > 0 && (
                        <div className="col-span-3 flex gap-2 overflow-x-auto items-center">
                            {cities.map(c => (
                                <button
                                    key={c.code}
                                    type="button"
                                    className="bg-blue-100 px-2 py-1 rounded text-xs hover:bg-blue-200 whitespace-nowrap"
                                    onClick={() => onSelectCity(c.nom)}
                                >
                                    {c.nom}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <input className="input col-span-4" name="address" placeholder="Adresse complète (Rue, Numéro, CP, Ville)" value={form.address} onChange={onChange} />
                <input className="input col-span-4" name="address2" placeholder="Adresse 2 (Facultatif)" value={form.address2} onChange={onChange} />

                <input className="input col-span-4" name="origin" placeholder="Origine du contact" value={form.origin} onChange={onChange} />
                <div className="col-span-4">
                    <div className="text-sm font-medium mb-2">Type de client</div>
                    <div className="flex items-center gap-4">
                        <label className="flex items-center gap-2 text-sm">
                            <input type="radio" name="type" value="prospect" checked={form.type === 'prospect'} onChange={onChange} />
                            Prospect
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                            <input type="radio" name="type" value="acquereur" checked={form.type === 'acquereur'} onChange={onChange} />
                            Acquéreur
                        </label>
                    </div>
                </div>
                <select className="input col-span-2" value={form.programme_id} onChange={(e) => onDrawerProgrammeChange(e.target.value)}>
                    <option value="">Programme (facultatif)</option>
                    {programmes.map(p => (
                        <option key={p.id} value={p.id}>{p.nom}</option>
                    ))}
                </select>
                <select className="input col-span-2" value={form.lot_id} onChange={(e) => setForm((prev) => ({ ...prev, lot_id: e.target.value }))} disabled={!form.programme_id}>
                    <option value="">Lot (facultatif)</option>
                    {drawerLots.map(l => (
                        <option key={l.id} value={l.id}>{l.lot || l.id}</option>
                    ))}
                </select>

                {!isEditing && (
                    <div className="col-span-4 border-t pt-3 mt-2">
                        <label className="flex items-center gap-2 text-sm font-medium cursor-pointer">
                            <input
                                type="checkbox"
                                checked={hasPartner}
                                onChange={(e) => setHasPartner(e.target.checked)}
                            />
                            Ajouter un(e) conjoint(e)
                        </label>
                    </div>
                )}
                {hasPartner && (
                    <div className="col-span-4 grid grid-cols-4 gap-3 border p-3 rounded bg-gray-50">
                        <div className="col-span-4 text-xs font-semibold text-gray-500">Conjoint(e)</div>
                        <div className="col-span-4">
                            <div className="flex items-center gap-4">
                                <label className="flex items-center gap-2 text-sm">
                                    <input type="radio" name="civility" value="M." checked={partner.civility === 'M.'} onChange={onPartnerChange} />
                                    M.
                                </label>
                                <label className="flex items-center gap-2 text-sm">
                                    <input type="radio" name="civility" value="Mme" checked={partner.civility === 'Mme'} onChange={onPartnerChange} />
                                    Mme
                                </label>
                            </div>
                        </div>
                        <input className="input col-span-2" name="last_name" placeholder="Nom" value={partner.last_name} onChange={onPartnerChange} />
                        <input className="input col-span-2" name="first_name" placeholder="Prénom" value={partner.first_name} onChange={onPartnerChange} />
                        <input className="input col-span-2" name="email" type="email" placeholder="Email" value={partner.email} onChange={onPartnerChange} />
                        <input className="input col-span-2" name="phone" placeholder="Téléphone" value={partner.phone} onChange={onPartnerChange} />
                    </div>
                )}

                <div className="col-span-4 flex justify-end gap-2 mt-4">
                    <button className="btn bg-white border" type="button" onClick={onClose} disabled={loading}>Annuler</button>
                    <button className="btn bg-blue-600 hover:bg-blue-700 text-white" disabled={loading}>
                        {loading ? 'Enregistrement...' : (isEditing ? 'Enregistrer' : 'Ajouter')}
                    </button>
                </div>
            </form>
        </Drawer>
    )
}
