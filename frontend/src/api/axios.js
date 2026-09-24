import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001'
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 et coupures réseau : message visible (une seule alerte par rafale
// d'erreurs), en plus du rejet normal pour que l'appelant garde la main.
let lastAlertAt = 0
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isLogin = (error.config?.url || '').includes('/auth/login')
    if (!error.response) {
      error.userMessage = "Impossible de joindre le serveur (connexion réseau interrompue ?). L'opération n'a pas été enregistrée."
    } else if (error.response.status === 401 && !isLogin) {
      error.userMessage = "Votre session a expiré. Reconnectez-vous puis recommencez : l'opération n'a pas été enregistrée."
    }
    if (error.userMessage && Date.now() - lastAlertAt > 3000) {
      lastAlertAt = Date.now()
      alert(error.userMessage)
    }
    return Promise.reject(error)
  }
)

// Message lisible pour l'utilisateur à partir d'une erreur axios.
export function apiErrorMessage(error, fallback) {
  if (error?.userMessage) return error.userMessage
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return `${fallback} (${detail})`
  if (Array.isArray(detail) && detail.length) {
    return `${fallback} (${detail.map(d => (d.msg || '').replace(/^Value error, /, '')).join(' ; ')})`
  }
  return fallback
}

export default api
