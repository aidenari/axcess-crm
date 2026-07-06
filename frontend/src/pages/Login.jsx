import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { username, password })
      const token = data?.access_token || data?.token
      if (!token) throw new Error('Token manquant dans la réponse du serveur')
      localStorage.setItem('token', token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Erreur de connexion')
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
        <h2 className="text-lg font-medium mb-4">Connexion</h2>
        {error && <div className="mb-3 text-sm text-red-600">{error}</div>}
        <div className="mb-4">
          <label className="block mb-1 text-sm">Nom d’utilisateur</label>
          <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="mb-6">
          <label className="block mb-1 text-sm">Mot de passe</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button className="btn w-full" disabled={loading}>
          {loading ? 'Connexion…' : 'Se connecter'}
        </button>
        <p className="mt-4 text-sm text-center">
          Pas de compte ? <Link to="/register" className="text-blue-700 hover:underline">Inscription</Link>
        </p>
      </form>
    </div>
  )
}
