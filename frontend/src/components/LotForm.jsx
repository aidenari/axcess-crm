import React, { useState, useEffect } from 'react'

const initial = (programmeId) => ({
    programme_id: programmeId || '',
    building: '',
    level: '',
    lot_number: '',
    typology: '',
    surface_hab: '',
    surface_total: '',
    price_total_ttc: '',
    status: 'Libre',
    client_name: '',
    seller: ''
})

export default function LotForm({ programmeId, onCreate }) {
    const [form, setForm] = useState(initial(programmeId))
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        setForm((f) => ({ ...f, programme_id: programmeId || '' }))
    }, [programmeId])

    const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

    const submit = async (e) => {
        e.preventDefault()
        if (!programmeId) return
        setLoading(true)
        const payload = {
            ...form,
            programme_id: programmeId,
            surface_hab: form.surface_hab ? Number(form.surface_hab) : null,
            surface_total: form.surface_total ? Number(form.surface_total) : null,
            price_total_ttc: form.price_total_ttc ? Number(form.price_total_ttc) : null
        }
        const res = await onCreate(payload)
        setLoading(false)
        if (res?.ok) setForm(initial(programmeId))
    }

    return (
        <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <div>
                <label className="block text-sm mb-1">Bâtiment</label>
                <input className="input" name="building" value={form.building} onChange={onChange} />
            </div>
            <div>
                <label className="block text-sm mb-1">Niveau</label>
                <input className="input" name="level" value={form.level} onChange={onChange} />
            </div>
            <div>
                <label className="block text-sm mb-1">N° lot</label>
                <input className="input" name="lot_number" value={form.lot_number} onChange={onChange} />
            </div>
            <div>
                <label className="block text-sm mb-1">Typologie</label>
                <input className="input" name="typology" value={form.typology} onChange={onChange} placeholder="T2, T3..." />
            </div>
            <div>
                <label className="block text-sm mb-1">Surface habitable</label>
                <input className="input" name="surface_hab" value={form.surface_hab} onChange={onChange} type="number" step="0.01" />
            </div>
            <div>
                <label className="block text-sm mb-1">Surface totale</label>
                <input className="input" name="surface_total" value={form.surface_total} onChange={onChange} type="number" step="0.01" />
            </div>
            <div>
                <label className="block text-sm mb-1">Prix TTC</label>
                <input className="input" name="price_total_ttc" value={form.price_total_ttc} onChange={onChange} type="number" />
            </div>
            <div>
                <label className="block text-sm mb-1">Statut</label>
                <select className="input" name="status" value={form.status} onChange={onChange}>
                    <option>Libre</option>
                    <option>Option</option>
                    <option>Réservé</option>
                    <option>Acté</option>
                </select>
            </div>
            <div>
                <label className="block text-sm mb-1">Acquéreur</label>
                <input className="input" name="client_name" value={form.client_name} onChange={onChange} />
            </div>
            <div>
                <label className="block text-sm mb-1">Vendeur</label>
                <input className="input" name="seller" value={form.seller} onChange={onChange} />
            </div>
            <div className="sm:col-span-3 lg:col-span-4 text-right">
                <button className="btn" disabled={!programmeId || loading}>{loading ? 'Création...' : 'Créer le lot'}</button>
            </div>
        </form>
    )
}
