import { useEffect, useState } from 'react'
import api from '../api/axios'
import { Link, useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [showLots, setShowLots] = useState(false)

  useEffect(() => {
    let mounted = true
      ; (async () => {
        try {
          const { data } = await api.get('/users/me')
          if (mounted) setProfile(data)
        } catch (err) {
          setError(err?.response?.data?.detail || 'Impossible de charger le profil')
          if (err?.response?.status === 401) {
            localStorage.removeItem('token')
            navigate('/login', { replace: true })
          }
        }
        try {
          const { data } = await api.get('/dashboard/stats')
          if (mounted) setStats(data || null)
        } catch {
          if (mounted) setStats(null)
        }
      })()
    return () => { mounted = false }
  }, [navigate])

  const formatMoney = (value) =>
    (value || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

  const counts = stats?.counts || {}
  const ca = stats?.ca || {}
  // Filter only Libre and Option
  const lots = (stats?.lots_disponibles || []).filter(l =>
    ['libre', 'option'].includes((l.statut || '').toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-xl font-semibold mb-2">Bienvenue{profile?.full_name ? `, ${profile.full_name}` : ''}</h2>
        {error && <div className="mb-3 text-sm text-red-600">{error}</div>}
        <div className="text-sm text-gray-600">
          Vous etes connecte en tant que {profile?.username || profile?.email} {profile?.role && `(role: ${profile.role})`}.
        </div>
      </div>

      <div className="card space-y-4">
        <div className="border-b pb-2">
          <h3 className="text-lg font-semibold">Chiffres d'affaires</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">CA total</div>
            <div className="text-2xl font-semibold">{formatMoney(ca.total)}</div>
          </div>
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">CA encaisse</div>
            <div className="text-2xl font-semibold">{formatMoney(ca.encaisse)}</div>
          </div>
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">CA restant</div>
            <div className="text-2xl font-semibold">{formatMoney(ca.restant)}</div>
          </div>
        </div>
      </div>

      <div className="card space-y-4">
        <div className="border-b pb-2 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Lots et disponibilites</h3>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{lots.length} lot(s)</span>
            <button className="btn" type="button" onClick={() => setShowLots((v) => !v)}>
              {showLots ? 'Masquer' : 'Afficher (Libre/Option)'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">Lots dispo</div>
            <div className="text-2xl font-semibold">{counts.disponible || 0}</div>
          </div>
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">Option</div>
            <div className="text-2xl font-semibold">{counts.option || 0}</div>
          </div>
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">Reserve</div>
            <div className="text-2xl font-semibold">{counts.reserve || 0}</div>
          </div>
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">Acte</div>
            <div className="text-2xl font-semibold">{counts.acte || 0}</div>
          </div>
          <div className="border rounded-lg p-4 bg-white">
            <div className="text-gray-500">Transit</div>
            <div className="text-2xl font-semibold">{counts.transit || 0}</div>
          </div>
        </div>

        {showLots && (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border">
              <thead className="bg-gray-50">
                <tr className="text-left">
                  <th className="p-2 border">Lot</th>
                  <th className="p-2 border">Programme</th>
                  <th className="p-2 border">Typologie</th>
                  <th className="p-2 border">Statut</th>
                  <th className="p-2 border">Prix</th>
                  <th className="p-2 border">Action</th>
                </tr>
              </thead>
              <tbody>
                {lots.map((lot) => (
                  <tr key={lot.id} className="hover:bg-gray-50">
                    <td className="p-2 border">{lot.lot || `Lot ${lot.id}`}</td>
                    <td className="p-2 border">{lot.programme_name}</td>
                    <td className="p-2 border">{lot.type}</td>
                    <td className="p-2 border">{lot.statut}</td>
                    <td className="p-2 border">{formatMoney(lot.prix_total)}</td>
                    <td className="p-2 border">
                      <Link className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700" to={`/grilles-de-prix/${lot.programme_id}?highlight_lot=${lot.id}`}>
                        Voir
                      </Link>
                    </td>
                  </tr>
                ))}
                {!lots.length && (
                  <tr>
                    <td className="p-3 text-sm text-gray-500" colSpan={6}>Aucun lot disponible.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <div className="font-medium mb-2">Liens rapides</div>
        <div className="flex flex-wrap gap-2">
          <Link to="/programmes" className="btn">Programmes</Link>
          <Link to="/grilles-de-prix/2" className="px-4 py-2 rounded-lg border">Grilles</Link>
          <Link to="/clients" className="px-4 py-2 rounded-lg border">Clients</Link>
        </div>
      </div>
    </div>
  )
}
