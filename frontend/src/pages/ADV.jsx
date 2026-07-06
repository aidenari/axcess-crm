import { useEffect, useState } from 'react'
import api from '../api/axios'

export default function ADV() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ programme_id:'', sru_deadline:'', deposit_status:'', financing_status:'', notary_meeting:'', notes:'', rank_index:'' })
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const load = async () => {
    try { const { data } = await api.get('/adv'); setItems(data || []) } catch { setItems([]) }
  }
  useEffect(()=>{ load() }, [])

  const create = async (e) => { e.preventDefault(); try { await api.post('/adv', form); setForm({ programme_id:'', sru_deadline:'', deposit_status:'', financing_status:'', notary_meeting:'', notes:'', rank_index:'' }); load() } catch { alert('Erreur création ADV') } }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">ADV</h1>
      <div className="card mb-6">
        <form onSubmit={create} className="grid grid-cols-3 gap-3">
          <input className="input" name="programme_id" placeholder="Programme" value={form.programme_id} onChange={onChange}/>
          <input className="input" name="sru_deadline" placeholder="Délai SRU" value={form.sru_deadline} onChange={onChange}/>
          <input className="input" name="deposit_status" placeholder="Dépôt de garantie" value={form.deposit_status} onChange={onChange}/>
          <input className="input" name="financing_status" placeholder="Statut financement" value={form.financing_status} onChange={onChange}/>
          <input className="input" type="date" name="notary_meeting" placeholder="RDV notaire" value={form.notary_meeting} onChange={onChange}/>
          <input className="input" name="rank_index" placeholder="Indice classement" value={form.rank_index} onChange={onChange}/>
          <input className="input col-span-3" name="notes" placeholder="Commentaires" value={form.notes} onChange={onChange}/>
          <div className="col-span-3 flex justify-end"><button className="btn">Ajouter</button></div>
        </form>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead className="bg-gray-50"><tr className="text-left">
            <th className="p-2 border">Programme</th>
            <th className="p-2 border">SRU</th>
            <th className="p-2 border">Dépôt</th>
            <th className="p-2 border">Financement</th>
            <th className="p-2 border">Notaire</th>
          </tr></thead>
          <tbody>
            {items.map(a => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="p-2 border">{a.programme_id}</td>
                <td className="p-2 border">{a.sru_deadline}</td>
                <td className="p-2 border">{a.deposit_status}</td>
                <td className="p-2 border">{a.financing_status}</td>
                <td className="p-2 border">{a.notary_meeting}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

