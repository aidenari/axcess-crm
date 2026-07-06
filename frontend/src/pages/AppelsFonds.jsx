import { useEffect, useState } from 'react'
import api from '../api/axios'

export default function AppelsFonds() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ programme_id:'', client_id:'', label:'', amount:'', due_date:'' })
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const load = async () => { try { const { data } = await api.get('/appels-fonds'); setItems(data || []) } catch { setItems([]) } }
  useEffect(()=>{ load() }, [])

  const create = async (e) => { e.preventDefault(); try { await api.post('/appels-fonds', form); setForm({ programme_id:'', client_id:'', label:'', amount:'', due_date:'' }); load() } catch { alert('Erreur création') } }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Appels de fonds</h1>
      <div className="card mb-6">
        <form onSubmit={create} className="grid grid-cols-5 gap-3">
          <input className="input" name="programme_id" placeholder="Programme" value={form.programme_id} onChange={onChange} />
          <input className="input" name="client_id" placeholder="Client" value={form.client_id} onChange={onChange} />
          <input className="input" name="label" placeholder="Libellé" value={form.label} onChange={onChange} />
          <input className="input" name="amount" placeholder="Montant" value={form.amount} onChange={onChange} />
          <input className="input" type="date" name="due_date" placeholder="Échéance" value={form.due_date} onChange={onChange} />
          <div className="col-span-5 flex justify-end"><button className="btn">Créer</button></div>
        </form>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead className="bg-gray-50"><tr className="text-left">
            <th className="p-2 border">Programme</th>
            <th className="p-2 border">Client</th>
            <th className="p-2 border">Libellé</th>
            <th className="p-2 border">Montant</th>
            <th className="p-2 border">Échéance</th>
          </tr></thead>
          <tbody>
            {items.map(i => (
              <tr key={i.id} className="hover:bg-gray-50">
                <td className="p-2 border">{i.programme_id}</td>
                <td className="p-2 border">{i.client_id}</td>
                <td className="p-2 border">{i.label}</td>
                <td className="p-2 border">{i.amount}</td>
                <td className="p-2 border">{i.due_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

