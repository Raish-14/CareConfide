import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageSquareText, Users, ShieldCheck } from 'lucide-react'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'

export default function PatientDashboard() {
  const { session } = useAuth()
  const [profile, setProfile] = useState(null)
  const [consultations, setConsultations] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.getPatientProfile(session.token).then(setProfile).catch((e) => setError(e.message))
    api.getPatientConsultations(session.token).then(setConsultations).catch(() => {})
  }, [session.token])

  return (
    <div className="max-w-4xl">
      <h1 className="font-display text-3xl text-ink">Welcome to CareConfide</h1>
      <p className="mt-2 text-ink-soft">
        {profile ? `You're signed in as ${profile.display_id}.` : 'Loading your profile…'}
      </p>
      {error && (
        <p className="mt-2 text-sm text-clay-600">{error}</p>
      )}

      <div className="mt-8">
        <Card className="flex flex-col items-start gap-4 bg-teal-50/60 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-xl text-ink">Have something on your mind?</h2>
            <p className="mt-1 text-sm text-ink-soft">Start a new consultation and describe it in your own words.</p>
          </div>
          <Link to="/patient/intake"><Button>Start a New Consultation</Button></Link>
        </Card>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Link to="/patient/intake">
          <Card className="h-full hover:border-teal-500/60">
            <MessageSquareText className="text-teal-500" size={22} strokeWidth={1.5} />
            <h3 className="mt-3 font-medium text-ink">New Concern</h3>
            <p className="mt-1 text-sm text-ink-soft">Begin an AI-assisted intake.</p>
          </Card>
        </Link>
        <Link to="/patient/matching">
          <Card className="h-full hover:border-teal-500/60">
            <Users className="text-teal-500" size={22} strokeWidth={1.5} />
            <h3 className="mt-3 font-medium text-ink">Find Care</h3>
            <p className="mt-1 text-sm text-ink-soft">Browse professionals suited to your concern.</p>
          </Card>
        </Link>
        <Link to="/patient/privacy">
          <Card className="h-full hover:border-teal-500/60">
            <ShieldCheck className="text-teal-500" size={22} strokeWidth={1.5} />
            <h3 className="mt-3 font-medium text-ink">Privacy</h3>
            <p className="mt-1 text-sm text-ink-soft">See how your information is handled.</p>
          </Card>
        </Link>
      </div>

      <div className="mt-10">
        <h2 className="font-display text-xl text-ink">Your consultations</h2>
        {consultations.length === 0 ? (
          <p className="mt-3 text-sm text-ink-soft">No consultations yet. Start a new concern above to begin.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {consultations.map((c) => (
              <Link key={c.id} to="/patient/consultation" state={{ consultationId: c.id }}>
                <Card className="flex items-center justify-between hover:border-teal-500/60">
                  <div>
                    <p className="font-medium text-ink">{c.concern_category || 'General concern'}</p>
                    <p className="text-sm text-ink-soft">with {c.professional_name}</p>
                  </div>
                  <span className="rounded-full bg-sage-100 px-3 py-1 text-xs capitalize text-ink-soft">{c.status}</span>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
