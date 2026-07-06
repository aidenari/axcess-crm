import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'

export default function Register() {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/users/register', {
        full_name: fullName,
        email,
        password
      })
      navigate('/login', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Erreur lors de l’inscription')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-6">
        <div className="mx-auto w-12 h-12 rounded-xl bg-blue-600 mb-3" />
        <h1 className="text-2xl font-semibold">Axcess CRM</h1>
      </div>
      <form onSubmit={handleSubmit} className="card">
        <h2 className="text-lg font-medium mb-4">Inscription</h2>
        {error && <div className="mb-3 text-sm text-red-600">{error}</div>}
        <div className="mb-4">
          <label className="block mb-1 text-sm">Nom complet</label>
          <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </div>
        <div className="mb-4">
          <label className="block mb-1 text-sm">Email</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="mb-6">
          <label className="block mb-1 text-sm">Mot de passe</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button className="btn w-full" disabled={loading}>
          {loading ? 'Inscription…' : 'Créer le compte'}
        </button>
        <p className="mt-4 text-sm text-center">
          Déjà un compte ? <Link to="/login" className="text-blue-700 hover:underline">Connexion</Link>
        </p>
      </form>
    </div>
  )
}
