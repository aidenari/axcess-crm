import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { Menu } from 'lucide-react'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Programmes from './pages/Programmes.jsx'
import GrillesDePrix from './pages/GrillesDePrix.jsx'
import Clients from './pages/Clients.jsx'
import LotsList from './pages/LotsList.jsx'
import ADV from './pages/ADV.jsx'
import AppelsFonds from './pages/AppelsFonds.jsx'
import Users from './pages/Users.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Sidebar from './components/Sidebar.jsx'

export default function App() {
  const token = localStorage.getItem('token')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()

  // Logic: 
  // - If sidebar is open: ml-64. If closed: ml-0.
  // - Width: max-w-[1200px] usually, BUT if sidebar is closed OR we are on 'grilles-de-prix', we want fluid width (w-full).
  const isGrillesDePrix = location.pathname.includes('/grilles-de-prix')
  const fluidWidth = !sidebarOpen || isGrillesDePrix

  return (
    <div className="min-h-screen flex relative">
      {token && <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />}

      {token && !sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow border hover:bg-gray-50"
          title="Ouvrir le menu"
        >
          <Menu size={20} />
        </button>
      )}

      <main className={`flex-1 px-6 py-6 transition-all duration-300 ${token ? (sidebarOpen ? 'ml-64' : 'ml-0') : 'max-w-xl mx-auto'} ${token ? (fluidWidth ? 'w-full' : 'max-w-[1200px]') : ''}`}>
        <Routes>
          <Route path="/" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/programmes" element={<ProtectedRoute><Programmes /></ProtectedRoute>} />
          <Route path="/grilles-de-prix" element={<Navigate to="/programmes" replace />} />
          {/** Route /grille-prix removed; use /grilles-de-prix/:programme_id */}
          <Route path="/grilles-de-prix/:programme_id" element={<ProtectedRoute><GrillesDePrix /></ProtectedRoute>} />
          <Route path="/clients" element={<ProtectedRoute><Clients /></ProtectedRoute>} />
          <Route path="/lots" element={<ProtectedRoute><LotsList /></ProtectedRoute>} />
          <Route path="/adv" element={<ProtectedRoute><ADV /></ProtectedRoute>} />
          <Route path="/appels-fonds" element={<ProtectedRoute><AppelsFonds /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><Users /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
