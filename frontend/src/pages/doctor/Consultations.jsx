import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'

export default function DoctorConsultations() {
  const { session } = useAuth()
  const [consultations, setConsultations] = useState([])

  useEffect(() => {
    api.getDoctorConsultations(session.token).then(setConsultations).catch(() => {})
  }, [session.token])

  return (
    <div className="max-w-4xl">
      <h1 className="font-display text-3xl text-ink">Consultations</h1>
      <p className="mt-2 text-ink-soft">All consultations assigned to you.</p>

      <div className="mt-6 space-y-3">
        {consultations.length === 0 && <p className="text-sm text-ink-soft">No consultations yet.</p>}
        {consultations.map((c) => (
          <Link key={c.id} to={`/doctor/consultation/${c.id}`}>
            <Card className="flex items-center justify-between hover:border-teal-500/60">
              <div>
                <p className="font-medium text-ink">{c.patient_display_id}</p>
                <p className="text-sm text-ink-soft">{c.concern_category} · {c.mode}</p>
              </div>
              <span className="rounded-full bg-sage-100 px-3 py-1 text-xs capitalize text-ink-soft">{c.status}</span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
