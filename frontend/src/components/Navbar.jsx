import { useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()

  const logout = () => {
    localStorage.removeItem('token')
    navigate('/login', { replace: true })
  }

  return (
    <header className="bg-white border-b">
      <div className="container mx-auto max-w-5xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600" />
          <span className="font-semibold">Axcess CRM</span>
        </div>
        <button className="btn" onClick={logout}>Déconnexion</button>
      </div>
    </header>
  )
}

