import { createContext, useContext, useState } from 'react'
import { Navigate } from 'react-router-dom'
import * as api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => api.getStoredUser())

  async function login(username, password) {
    const data = await api.login(username, password)
    api.saveSession(data.access_token, data.user)
    setUser(data.user)
    return data.user
  }

  function logout() {
    api.clearSession()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

// Guards routes that require an authenticated session.
export function ProtectedRoute({ children }) {
  const { user } = useAuth()
  if (!user || !api.getToken()) {
    return <Navigate to="/login" replace />
  }
  return children
}
