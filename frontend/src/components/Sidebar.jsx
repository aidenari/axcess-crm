import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Building2, Grid3X3, List, Users, ClipboardList, Wallet, UserCog, LogOut, X } from 'lucide-react'
import api from '../api/axios'
import { useEffect, useState } from 'react'

export default function Sidebar({ open = true, onClose }) {
  const navigate = useNavigate()
  const [role, setRole] = useState(null)
  const [name, setName] = useState('')

  useEffect(() => {
    let mounted = true
      ; (async () => {
        try {
          const { data } = await api.get('/users/me')
          if (mounted) {
            setRole(data.role || null)
            setName(data.full_name || data.username || data.email || '')
            // cache for reuse
            localStorage.setItem('user_me', JSON.stringify(data))
          }
        } catch {
          // ignore; ProtectedRoute will redirect if token invalid
        }
      })()
    return () => {
      mounted = false
    }
  }, [])

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user_me')
    navigate('/login', { replace: true })
  }

  const linkClass = ({ isActive }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-blue-50 ${isActive ? 'bg-blue-100 text-blue-700' : 'text-gray-700'
    }`

  return (
    <aside className={`h-screen border-r bg-white p-4 fixed top-0 left-0 overflow-y-auto transition-transform duration-300 z-40 w-64 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex items-center justify-between gap-2 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex-shrink-0" />
          <div className="overflow-hidden">
            <div className="font-semibold whitespace-nowrap">Axcess CRM</div>
            {name && (
              <div className="text-xs text-gray-500 truncate max-w-[8rem]">
                {name}
              </div>
            )}
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded text-gray-500">
          <X size={18} />
        </button>
      </div>

      <nav className="space-y-1">
        <NavLink to="/dashboard" className={linkClass}>
          <LayoutDashboard size={18} />Tableau de bord
        </NavLink>
        <NavLink to="/programmes" className={linkClass}>
          <Building2 size={18} />Programmes
        </NavLink>
        <NavLink to="/grilles-de-prix/2" className={linkClass}>
          <Grid3X3 size={18} />Grilles de prix
        </NavLink>
        <NavLink to="/lots" className={linkClass}>
          <List size={18} />Liste des lots
        </NavLink>
        <NavLink to="/clients" className={linkClass}>
          <Users size={18} />Clients
        </NavLink>
        <NavLink to="/adv" className={linkClass}>
          <ClipboardList size={18} />ADV
        </NavLink>
        <NavLink to="/appels-fonds" className={linkClass}>
          <Wallet size={18} />Appels de fonds
        </NavLink>
        {role === 'super_utilisateur' && (
          <NavLink to="/users" className={linkClass}>
            <UserCog size={18} />Gestion utilisateurs
          </NavLink>
        )}
      </nav>

      <div className="mt-6">
        <button className="btn w-full flex gap-2" onClick={logout}>
          <LogOut size={18} />Déconnexion
        </button>
      </div>
    </aside>
  )
}
