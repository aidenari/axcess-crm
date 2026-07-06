import React from 'react'

export default function Filters({ filters, setFilters, typologies = [], buildings = [] }) {
  const set = (key, value) => setFilters(prev => ({ ...prev, [key]: value }))

  return (
    <div className="flex flex-wrap gap-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Statut</span>
        <select className="input" value={filters.status} onChange={(e)=>set('status', e.target.value)}>
          {['Tous','Libre','Option','Réservé','Acté'].map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Typologie</span>
        <select className="input" value={filters.typology} onChange={(e)=>set('typology', e.target.value)}>
          <option value="Tous">Tous</option>
          {typologies.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Bâtiment</span>
        <select className="input" value={filters.building} onChange={(e)=>set('building', e.target.value)}>
          <option value="Tous">Tous</option>
          {buildings.map(b => <option key={b} value={b}>{b}</option>)}
        </select>
      </div>
    </div>
  )
}

