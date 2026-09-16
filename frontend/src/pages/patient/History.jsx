import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'

export default function History() {
  const { session } = useAuth()
  const [profiles, setProfiles] = useState([])
  const [consultations, setConsultations] = useState([])

  useEffect(() => {
    api.getClinicalProfiles(session.token).then(setProfiles).catch(() => {})
    api.getPatientConsultations(session.token).then(setConsultations).catch(() => {})
  }, [session.token])

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-3xl text-ink">History</h1>
      <p className="mt-2 text-ink-soft">Past intakes and consultations linked to your account.</p>

      <h2 className="mt-8 font-display text-xl text-ink">Clinical summaries</h2>
      <div className="mt-3 space-y-3">
        {profiles.length === 0 && <p className="text-sm text-ink-soft">No confirmed intakes yet.</p>}
        {profiles.map((p) => (
          <Card key={p.id}>
            <p className="font-medium text-ink">{p.concern_category}</p>
            <p className="mt-1 text-sm text-ink-soft">{p.ai_summary}</p>
            <p className="mt-2 text-xs text-ink-faint">Duration: {p.duration}</p>
          </Card>
        ))}
      </div>

      <h2 className="mt-8 font-display text-xl text-ink">Consultations</h2>
      <div className="mt-3 space-y-3">
        {consultations.length === 0 && <p className="text-sm text-ink-soft">No consultations yet.</p>}
        {consultations.map((c) => (
          <Link key={c.id} to="/patient/consultation" state={{ consultationId: c.id }}>
            <Card className="flex items-center justify-between hover:border-teal-500/60">
              <div>
                <p className="font-medium text-ink">{c.concern_category}</p>
                <p className="text-sm text-ink-soft">with {c.professional_name}</p>
              </div>
              <span className="rounded-full bg-sage-100 px-3 py-1 text-xs capitalize text-ink-soft">{c.status}</span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
