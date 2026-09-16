import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'
import { api, ApiError } from '../services/api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [demoAccounts, setDemoAccounts] = useState([])
  const { login } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    api.demoAccounts().then((d) => setDemoAccounts(d.accounts)).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.login({ email, password })
      login(res)
      navigate(res.role === 'professional' ? '/doctor/dashboard' : '/patient/dashboard')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const useDemo = (account) => {
    setEmail(account.email)
    setPassword('demo1234')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-sage-50 px-6">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 block text-center"><Logo className="text-2xl" /></Link>
        <Card>
          <h1 className="font-display text-2xl text-ink">Welcome back</h1>
          <p className="mt-1 text-sm text-ink-soft">Log in to continue your care, privately.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
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
                type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
              />
            </div>
            {error && <p className="text-sm text-clay-600">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Logging in…' : 'Log in'}
            </Button>
          </form>

          {demoAccounts.length > 0 && (
            <div className="mt-6 border-t border-sage-200 pt-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-ink-faint">Try a demo account</p>
              <div className="flex flex-wrap gap-2">
                {demoAccounts.map((a) => (
                  <button
                    key={a.email} type="button" onClick={() => useDemo(a)}
                    className="rounded-full border border-sage-200 px-3 py-1 text-xs text-ink-soft hover:border-teal-500 hover:text-teal-600"
                  >
                    {a.label}
                  </button>
                ))}
              </div>
              <p className="mt-2 text-xs text-ink-faint">Any password works for demo accounts.</p>
            </div>
          )}

          <p className="mt-6 text-center text-sm text-ink-soft">
            New here? <Link to="/register" className="text-teal-600 hover:underline">Create an account</Link>
          </p>
        </Card>
      </div>
    </div>
  )
}
