import React, { useEffect, useMemo, useRef } from 'react'
import { isReadOnly } from '../utils/auth'
import { formatDate } from '../utils/formatDate'

const statusColors = {
  'Libre': 'bg-white text-gray-900',
  'Option': 'bg-green-100 text-green-800',
  'Réservation': 'bg-red-100 text-red-800',
  'Réservé': 'bg-red-100 text-red-800',
  'Acté': 'bg-blue-100 text-blue-800'
}

function toInputDate(v) {
  if (!v) return ''
  if (/^\d{4}-\d{2}-\d{2}/.test(v)) return v.slice(0, 10)
  const m = String(v).match(/(\d{2})\/(\d{2})\/(\d{4})/)
  if (m) return `${m[3]}-${m[2]}-${m[1]}`
  const d = new Date(v)
  if (isNaN(d)) return ''
  return d.toISOString().slice(0, 10)
}

export default function LotRow({ lot, onUpdate, statusDisplayMap, statusSendMap, variant = 'simple', onEdit, clients = [], highlight = false }) {
  const readOnly = isReadOnly()
  const displayStatus = useMemo(() => statusDisplayMap?.[lot.status] || lot.status || lot.statut || 'Libre', [lot.status, lot.statut, statusDisplayMap])

  const rowRef = useRef(null)
  const highlightClass = highlight ? 'bg-yellow-100' : ''

  useEffect(() => {
    if (highlight && rowRef.current) {
      rowRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [highlight])

  const onBlurNumber = (field) => (e) => {
    const raw = e.target.value
    const value = raw === '' ? null : Number(raw)
    onUpdate(lot.id, { [field]: value })
  }
  const onBlurText = (field) => (e) => onUpdate(lot.id, { [field]: e.target.value })

  if (variant === 'project') {
    const formatMoney = (val) => (val || 0).toLocaleString('fr-FR', { style: 'currency', currency: 'EUR' })

    // Frontend Calculations
    const p_logement = Number(lot.prix_logement) || 0
    const p_total = Number(lot.prix_total) || 0
    const surface = Number(lot.sha_m2) || 0

    const calc_m2_appart = surface > 0 ? p_logement / surface : 0
    const calc_m2_parking = surface > 0 ? p_total / surface : 0

    // Status Sanitization
    let stVal = lot.statut || displayStatus
    if (stVal && stVal.includes('servation')) stVal = 'Réservation'
    if (stVal && stVal.includes('serv') && !stVal.includes('ation')) stVal = 'Réservé'

    const getStatusClass = (s) => {
      const lower = (s || '').toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      if (lower.includes('libre')) return 'text-gray-600'
      if (lower.includes('option')) return 'bg-green-100 text-green-800'
      if (lower.includes('reserv')) return 'bg-red-100 text-red-800'
      if (lower.includes('acte')) return 'bg-blue-100 text-blue-800'
      return 'text-gray-600'
    }

    return (
      <tr ref={rowRef} className={`hover:bg-gray-50 transition-colors ${getStatusClass(stVal)} ${highlightClass}`}>
        <td className="p-2 border">{lot.lot}</td>
        <td className="p-2 border">{lot.niveau}</td>
        <td className="p-2 border">{lot.type}</td>
        <td className="p-2 border">{lot.surface_sol}</td>
        <td className="p-2 border">{lot.sha_m2}</td>
        <td className="p-2 border">{lot.orientation}</td>
        <td className="p-2 border min-w-[140px]">
          {lot.annexes?.length
            ? lot.annexes.map(a => `${a.type}${a.numero ? ' ' + a.numero : ''}`).join(', ')
            : <span className="text-gray-400">—</span>}
        </td>
        <td className="p-2 border">{lot.jardin || '-'}</td>
        <td className="p-2 border">{lot.terrasse || '-'}</td>
        <td className="p-2 border min-w-[120px] text-right font-medium text-gray-600">{formatMoney(lot.prix_logement)}</td>
        <td className="p-2 border min-w-[120px] text-right font-medium text-gray-600">{formatMoney(lot.prix_stationnement)}</td>
        <td className="p-2 border min-w-[120px] text-right font-bold text-blue-900">{formatMoney(lot.prix_total)}</td>
        <td className="p-2 border">{calc_m2_appart > 0 ? formatMoney(calc_m2_appart) : '-'}</td>
        <td className="p-2 border">{calc_m2_parking > 0 ? formatMoney(calc_m2_parking) : '-'}</td>
        <td className="p-2 border min-w-[180px]">
          {(() => {
            const name = lot.dossier_noms
              || (lot.acquereurs?.length ? lot.acquereurs.join(' + ') : null)
              || lot.acquereur
            return name
              ? <span className="font-semibold text-blue-800">{name}</span>
              : <span className="text-gray-400 italic">Aucun</span>
          })()}
        </td>
        <td className="p-2 border">
          <span className={`px-2 py-1 rounded text-xs font-semibold ${getStatusClass(stVal)}`}>
            {stVal}
          </span>
        </td>
        <td className="p-2 border whitespace-nowrap">{formatDate(lot.date_reservation) || '-'}</td>
        <td className="p-2 border whitespace-nowrap">{formatDate(lot.date_acte) || '-'}</td>
        <td className="p-2 border text-right">
          {!readOnly && (
            <button className="btn bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 text-xs rounded" onClick={() => onEdit?.(lot)}>Modifier</button>
          )}
        </td>
      </tr>
    )
  }

  const onChangeStatus = (e) => {
    const displayed = e.target.value
    const backendValue = statusSendMap?.[displayed] ?? displayed
    onUpdate(lot.id, { status: backendValue })
  }

  return (
    <tr ref={rowRef} className={`hover:bg-gray-50 transition-colors ${statusColors[displayStatus] || ''} ${highlightClass}`}>
      <td className="p-2 border whitespace-nowrap">{lot.building}-{lot.level}-{lot.lot_number}</td>
      <td className="p-2 border">{lot.typology}</td>
      <td className="p-2 border">{lot.level}</td>
      <td className="p-2 border">{lot.surface_hab} / {lot.surface_total}</td>
      <td className="p-2 border min-w-[130px]">
        <input type="number" className="input" defaultValue={lot.price_total_ttc ?? ''} onBlur={onBlurNumber('price_total_ttc')} disabled={readOnly} />
      </td>
      <td className="p-2 border min-w-[180px]">
        <input type="text" className="input" defaultValue={lot.client_name ?? ''} placeholder="Acquéreur" onBlur={onBlurText('client_name')} disabled={readOnly} />
      </td>
      <td className="p-2 border">
        <select className="input" value={displayStatus} onChange={onChangeStatus} disabled={readOnly}>
          {['Libre', 'Option', 'Réservé', 'Acté'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </td>
      <td className="p-2 border min-w-[150px]">
        <input type="date" className="input" defaultValue={toInputDate(lot.date_acte)} onBlur={(e) => onUpdate(lot.id, { date_acte: e.target.value || null })} disabled={readOnly} />
      </td>
      <td className="p-2 border text-right"></td>
    </tr>
  )
}
