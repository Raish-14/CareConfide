import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'
import { api, ApiError } from '../services/api'

export default function Register() {
  const [params] = useSearchParams()
  const initialRole = params.get('role') === 'professional' ? 'professional' : 'patient'
  const [role, setRole] = useState(initialRole)
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [specialty, setSpecialty] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.register({
        email, password, role, full_name: fullName,
        ...(role === 'professional' ? { specialty } : {}),
      })
      login(res)
      navigate(role === 'professional' ? '/doctor/dashboard' : '/patient/dashboard')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-sage-50 px-6 py-12">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 block text-center"><Logo className="text-2xl" /></Link>
        <Card>
          <h1 className="font-display text-2xl text-ink">Create your account</h1>
          <p className="mt-1 text-sm text-ink-soft">
            CareConfide is privacy-first, not anonymous — some identity information is required for compliant care.
          </p>

          <div className="mt-5 flex rounded-full border border-sage-200 p-1 text-sm">
            {['patient', 'professional'].map((r) => (
              <button
                key={r} type="button" onClick={() => setRole(r)}
                className={`flex-1 rounded-full py-1.5 capitalize transition-colors ${
                  role === r ? 'bg-teal-500 text-sage-50' : 'text-ink-soft'
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div>
              <label className="mb-1 block text-sm text-ink-soft">Full name</label>
              <input
                required value={fullName} onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-lg border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
              />
            </div>
            {role === 'professional' && (
              <div>
                <label className="mb-1 block text-sm text-ink-soft">Specialty</label>
                <input
                  required value={specialty} onChange={(e) => setSpecialty(e.target.value)}
                  placeholder="e.g. Mental Health & Counseling"
                  className="w-full rounded-lg border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
                />
              </div>
            )}
            <div>
              <label className="mb-1 block text-sm text-ink-soft">Email</label>
              <input
                type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-ink-soft">Password</label>
              <input
                type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
              />
            </div>
            {error && <p className="text-sm text-clay-600">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Creating account…' : 'Create account'}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-ink-soft">
            Already have an account? <Link to="/login" className="text-teal-600 hover:underline">Log in</Link>
          </p>
        </Card>
      </div>
    </div>
  )
}
