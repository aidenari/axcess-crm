import React from 'react'

export default function StatsBar({ stats }) {
  const total = stats?.lots_total ?? stats?.total_lots ?? stats?.total ?? 0
  const actes = stats?.actes ?? 0
  const options = stats?.options ?? 0
  const reservations = stats?.reservations ?? 0
  // Libres est calculé par soustraction pour cohérence visuelle
  const occupied = actes + options + reservations
  const libres = Math.max(0, total - occupied)

  const caTotal = stats?.ca_total ?? 0
  const caActes = stats?.ca_actes ?? 0
  const caRes = stats?.ca_reservations ?? 0

  const getPct = (val) => total ? Math.round((val / total) * 100) : 0
  const getCaPct = (val) => caTotal ? Math.round((val / caTotal) * 100) : 0

  const formatEuro = (val) => (val || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })

  return (
    <div className="card">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 items-start mb-4">
        <div>
          <div className="text-sm text-gray-600 mb-1">Lots</div>
          <div className="text-2xl font-bold text-gray-800">{total}</div>
        </div>
        <div>
          <div className="text-sm text-gray-600 mb-1">Actes</div>
          <div className="text-2xl font-bold text-blue-600">{actes} <span className="text-sm font-normal text-gray-500">({getPct(actes)}%)</span></div>
          {caActes > 0 && (
            <div className="text-xs text-blue-600 mt-1" title="CA Acté">
              {formatEuro(caActes)} ({getCaPct(caActes)}%)
            </div>
          )}
        </div>
        <div>
          <div className="text-sm text-gray-600 mb-1">Réservations</div>
          <div className="text-2xl font-bold text-red-600">{reservations} <span className="text-sm font-normal text-gray-500">({getPct(reservations)}%)</span></div>
          {caRes > 0 && (
            <div className="text-xs text-red-600 mt-1" title="CA Réservé">
              {formatEuro(caRes)} ({getCaPct(caRes)}%)
            </div>
          )}
        </div>
        <div>
          <div className="text-sm text-gray-600 mb-1">Options</div>
          <div className="text-2xl font-bold text-green-600">{options} <span className="text-sm font-normal text-gray-500">({getPct(options)}%)</span></div>
        </div>
        <div>
          <div className="text-sm text-gray-600 mb-1">CA total</div>
          <div className="text-2xl font-bold text-gray-800">{formatEuro(caTotal)}</div>
          <div className="text-xs text-gray-500 mt-1">
            Sécurisé: {getCaPct(caActes + caRes)}%
          </div>
        </div>
      </div>

      {/* Stacked Progress Bar */}
      <div className="w-full bg-gray-100 rounded-full h-3 flex overflow-hidden">
        {actes > 0 && <div className="bg-blue-600 h-full" style={{ width: `${(actes / total) * 100}%` }} title={`Actes: ${actes}`} />}
        {reservations > 0 && <div className="bg-red-600 h-full" style={{ width: `${(reservations / total) * 100}%` }} title={`Réservations: ${reservations}`} />}
        {options > 0 && <div className="bg-green-600 h-full" style={{ width: `${(options / total) * 100}%` }} title={`Options: ${options}`} />}
      </div>

      <div className="flex justify-between text-xs text-gray-500 mt-2">
        <div className="flex gap-3">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-600"></span> Actés</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-600"></span> Réservés</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-600"></span> Options</span>
        </div>
        <span>Libres: {libres}</span>
      </div>
    </div>
  )
}

