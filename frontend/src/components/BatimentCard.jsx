import React from 'react'
import GrilleTable from './GrilleTable.jsx'

export default function BatimentCard({ batiment, filters, onLotsChanged, onAddBatimentClick, highlightLotId, onBatimentUpdated, onBatimentDeleted }) {
  return (
    <GrilleTable
      batiment={batiment}
      filters={filters}
      onChanged={onLotsChanged}
      onAddBatimentClick={onAddBatimentClick}
      highlightLotId={highlightLotId}
      onBatimentUpdated={onBatimentUpdated}
      onBatimentDeleted={onBatimentDeleted}
    />
  )
}
