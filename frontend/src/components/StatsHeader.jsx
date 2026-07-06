import React from 'react'

function formatCurrencyEUR(value) {
    const n = typeof value === 'number' ? value : Number(value || 0)
    return n.toLocaleString('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 })
}

export default function StatsHeader({ stats }) {
    const totalLots = stats?.total_lots ?? stats?.total ?? stats?.count ?? 0
    const caTotal = stats?.ca_total ?? stats?.total_revenue ?? stats?.revenue_total ?? 0
    const byStatus = stats?.by_status || stats?.status_counts || stats?.statuses || {}

    const libres = byStatus['Libre'] ?? byStatus['Disponible'] ?? 0
    const options = byStatus['Option'] ?? 0
    const reserves = byStatus['Réservé'] ?? byStatus['Réservation'] ?? byStatus['Transit'] ?? 0
    const actes = byStatus['Acté'] ?? 0

    const pc = (n) => totalLots ? Math.round((n * 1000) / totalLots) / 10 : 0

    const cards = [
        { label: 'Total lots', value: totalLots, bar: 100, color: 'bg-gray-300' },
        { label: 'CA total', value: formatCurrencyEUR(caTotal), bar: 100, color: 'bg-blue-600' },
        { label: 'Libres', value: `${libres} • ${pc(libres)}%`, bar: pc(libres), color: 'bg-gray-400' },
        { label: 'Option', value: `${options} • ${pc(options)}%`, bar: pc(options), color: 'bg-green-600' },
        { label: 'Réservés', value: `${reserves} • ${pc(reserves)}%`, bar: pc(reserves), color: 'bg-red-600' },
        { label: 'Actés', value: `${actes} • ${pc(actes)}%`, bar: pc(actes), color: 'bg-blue-600' },
    ]

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {cards.map((c, idx) => (
                <div key={idx} className="bg-white rounded-xl border p-4">
                    <div className="text-sm text-gray-600">{c.label}</div>
                    <div className="text-xl font-semibold mt-1">{c.value}</div>
                    <div className="mt-3 h-2 w-full bg-gray-200 rounded">
                        <div className={`${c.color} h-2 rounded`} style={{ width: `${Math.min(100, c.bar)}%` }} />
                    </div>
                </div>
            ))}
        </div>
    )
}
