import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'

export default function DoctorDashboard() {
  const { session } = useAuth()
  const [consultations, setConsultations] = useState([])

  useEffect(() => {
    api.getDoctorConsultations(session.token).then(setConsultations).catch(() => {})
  }, [session.token])

  const incoming = consultations.filter((c) => c.status === 'requested')
  const active = consultations.filter((c) => c.status === 'active' || c.status === 'accepted')

  return (
    <div className="max-w-4xl">
      <h1 className="font-display text-3xl text-ink">Professional Dashboard</h1>
      <p className="mt-2 text-ink-soft">Welcome back, {session.displayName}.</p>

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Card>
          <p className="text-xs uppercase tracking-wide text-ink-faint">Incoming</p>
          <p className="mt-2 font-display text-3xl text-ink">{incoming.length}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-ink-faint">Active</p>
          <p className="mt-2 font-display text-3xl text-ink">{active.length}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-ink-faint">Availability</p>
          <p className="mt-2 text-sm text-ink-soft">Weekdays 10am – 4pm</p>
        </Card>
      </div>

      <h2 className="mt-10 font-display text-xl text-ink">Incoming consultations</h2>
      <div className="mt-3 space-y-3">
        {incoming.length === 0 && <p className="text-sm text-ink-soft">Nothing waiting right now.</p>}
        {incoming.map((c) => (
          <Link key={c.id} to={`/doctor/consultation/${c.id}`}>
            <Card className="flex items-center justify-between hover:border-teal-500/60">
              <div>
                <p className="font-medium text-ink">{c.patient_display_id}</p>
                <p className="text-sm text-ink-soft">{c.concern_category}</p>
              </div>
              <span className="rounded-full bg-sage-100 px-3 py-1 text-xs capitalize text-ink-soft">{c.status}</span>
            </Card>
          </Link>
        ))}
      </div>

      <h2 className="mt-10 font-display text-xl text-ink">Active consultations</h2>
      <div className="mt-3 space-y-3">
        {active.length === 0 && <p className="text-sm text-ink-soft">No active consultations.</p>}
        {active.map((c) => (
          <Link key={c.id} to={`/doctor/consultation/${c.id}`}>
            <Card className="flex items-center justify-between hover:border-teal-500/60">
              <div>
                <p className="font-medium text-ink">{c.patient_display_id}</p>
                <p className="text-sm text-ink-soft">{c.concern_category}</p>
              </div>
              <span className="rounded-full bg-teal-50 px-3 py-1 text-xs capitalize text-teal-700">{c.status}</span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
