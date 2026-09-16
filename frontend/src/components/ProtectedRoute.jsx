import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ProtectedRoute({ role, children }) {
  const { session } = useAuth()

  if (!session) return <Navigate to="/login" replace />
  if (role && session.role !== role) {
    return <Navigate to={session.role === 'professional' ? '/doctor/dashboard' : '/patient/dashboard'} replace />
  }
  return children
}
