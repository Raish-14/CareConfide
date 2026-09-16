import { createContext, useContext, useEffect, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => {
    const raw = localStorage.getItem('careconfide_session')
    return raw ? JSON.parse(raw) : null
  })

  useEffect(() => {
    if (session) {
      localStorage.setItem('careconfide_session', JSON.stringify(session))
    } else {
      localStorage.removeItem('careconfide_session')
    }
  }, [session])

  const login = (authResponse) => {
    setSession({
      token: authResponse.access_token,
      role: authResponse.role,
      userId: authResponse.user_id,
      displayName: authResponse.display_name,
    })
  }

  const logout = () => setSession(null)

  return (
    <AuthContext.Provider value={{ session, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
