import { useEffect, useState } from 'react'
import api from '../api/axios'

export default function Users() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ username:'', email:'', full_name:'', role:'commercial', password:'' })
  const [forbidden, setForbidden] = useState(false)
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const roleOptions = [
    { value: 'super_utilisateur', label: 'Super utilisateur' },
    { value: 'admin', label: 'Admin' },
    { value: 'commercial', label: 'Commercial' },
    { value: 'lecture_seule', label: 'Lecture seule' },
  ]

  const labelForRole = (value) =>
    (roleOptions.find((opt) => opt.value === (value || '').toLowerCase()) || {}).label || 'Commercial'

  const load = async () => {
    try {
      const { data } = await api.get('/users')
      setItems(data || [])
      setForbidden(false)
    } catch (err) {
      setItems([])
      setForbidden(err?.response?.status === 403)
    }
  }
  useEffect(() => { load() }, [])

  const create = async (e) => {
    e.preventDefault()
    try {
      await api.post('/users', form)
      setForm({ username:'', email:'', full_name:'', role:'commercial', password:'' })
      load()
    } catch {
      alert('Erreur creation utilisateur')
    }
  }

  const changeRole = async (id, role) => { try { await api.put(`/users/${id}`, { role }); load() } catch { alert('Erreur role') } }
  const changePassword = async (id) => {
    const password = prompt('Nouveau mot de passe')
    if (!password) return
    try { await api.put(`/users/${id}`, { password }); alert('Mot de passe mis a jour') } catch { alert('Erreur mot de passe') }
  }
  const removeItem = async (id) => { if(!confirm('Supprimer ?')) return; try { await api.delete(`/users/${id}`); setItems(items.filter(i=>i.id!==id)) } catch { alert('Erreur suppression') } }

  if (forbidden) {
    return (
      <div className="card">
        <h1 className="text-2xl font-semibold mb-2">Acces interdit</h1>
        <p>Cette page est reservee au super utilisateur.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Utilisateurs</h1>
      <div className="card mb-6">
        <form onSubmit={create} className="grid grid-cols-5 gap-3">
          <input className="input" name="username" placeholder="Nom utilisateur" value={form.username} onChange={onChange} required />
          <input className="input" name="email" placeholder="Email" value={form.email} onChange={onChange} />
          <input className="input" name="full_name" placeholder="Nom complet" value={form.full_name} onChange={onChange} />
          <select className="input" name="role" value={form.role} onChange={onChange}>
            {roleOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <input className="input" type="password" name="password" placeholder="Mot de passe" value={form.password} onChange={onChange} />
          <div className="col-span-5 flex justify-end"><button className="btn">Ajouter</button></div>
        </form>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border">
          <thead className="bg-gray-50"><tr className="text-left">
            <th className="p-2 border">Utilisateur</th>
            <th className="p-2 border">Email</th>
            <th className="p-2 border">Role</th>
            <th className="p-2 border">Actions</th>
          </tr></thead>
          <tbody>
            {items.map(u => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="p-2 border">{u.username || u.full_name}</td>
                <td className="p-2 border">{u.email}</td>
                <td className="p-2 border">{labelForRole(u.role)}</td>
                <td className="p-2 border space-x-2">
                  <select className="input" value={(u.role || 'commercial').toLowerCase()} onChange={e=>changeRole(u.id, e.target.value)}>
                    {roleOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                  <button className="text-blue-600 hover:underline" onClick={()=>changePassword(u.id)}>Mot de passe</button>
                  <button className="text-red-600 hover:underline" onClick={()=>removeItem(u.id)}>Supprimer</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
