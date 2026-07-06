import React from 'react'
import LotRow from './LotRow.jsx'

export default function GrillePrixTable({ lots = [], onUpdate, statusDisplayMap, statusSendMap }) {
    return (
        <table className="w-full text-sm border-collapse">
            <thead className="bg-gray-100 text-gray-700">
                <tr className="text-left">
                    <th className="p-2 border">Lot</th>
                    <th className="p-2 border">Typologie</th>
                    <th className="p-2 border">Niveau</th>
                    <th className="p-2 border">Surface (hab/total)</th>
                    <th className="p-2 border">Prix TTC</th>
                    <th className="p-2 border">Client</th>
                    <th className="p-2 border">Statut</th>
                    <th className="p-2 border">Date acte</th>
                    <th className="p-2 border">Actions</th>
                </tr>
            </thead>
            <tbody>
                {lots.map(lot => (
                    <LotRow key={lot.id} lot={lot} onUpdate={onUpdate} statusDisplayMap={statusDisplayMap} statusSendMap={statusSendMap} />
                ))}
                {!lots.length && (
                    <tr>
                        <td className="p-4 text-center text-gray-500" colSpan={9}>Aucun lot à afficher</td>
                    </tr>
                )}
            </tbody>
        </table>
    )
}
