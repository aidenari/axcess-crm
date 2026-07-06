import { useState, useEffect } from 'react'
import api from '../api/axios'

export default function EditBatimentModal({ open, onClose, batiment, onSaved }) {
    const [nom, setNom] = useState('')
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (open && batiment) {
            setNom(batiment.nom || batiment.name || '')
        }
    }, [open, batiment])

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!batiment) return
        setLoading(true)
        try {
            // payload matches BatimentCreate: { nom, programme_id }
            // We keep existing programme_id.
            await api.put(`/batiments/${batiment.id}`, {
                nom,
                programme_id: batiment.programme_id
            })
            onSaved?.({ ...batiment, nom })
            onClose()
        } catch (e) {
            console.error(e)
            alert("Erreur lors de la modification")
        } finally {
            setLoading(false)
        }
    }

    if (!open) return null

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
                <h2 className="text-xl font-semibold mb-4">Modifier le bâtiment</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nom du bâtiment</label>
                        <input
                            type="text"
                            required
                            className="input w-full"
                            value={nom}
                            onChange={(e) => setNom(e.target.value)}
                        />
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                        <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
                            Annuler
                        </button>
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? 'Enregistrement...' : 'Enregistrer'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
