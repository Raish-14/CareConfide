import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { ChevronDown, ChevronUp } from 'lucide-react'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { useAuth } from '../../hooks/useAuth'
import { api, ApiError } from '../../services/api'

function Field({ label, value }) {
  const display = Array.isArray(value) ? value.filter(Boolean).join(', ') : value
  if (!display) return null
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-ink-faint">{label}</p>
      <p className="mt-1 text-sm text-ink">{display}</p>
    </div>
  )
}

export default function Review() {
  const { session } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { sessionId, structured } = location.state || {}

  const [notes, setNotes] = useState('')
  const [identityOpen, setIdentityOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!sessionId || !structured) {
    return (
      <div className="max-w-2xl">
        <Card>
          <p className="text-ink-soft">
            There's no intake to review yet. <Link to="/patient/intake" className="text-teal-600 hover:underline">Start a new concern</Link> first.
          </p>
        </Card>
      </div>
    )
  }

  const handleConfirm = async () => {
    setLoading(true)
    setError('')
    try {
      const profile = await api.confirmIntake(session.token, { session_id: sessionId, additional_notes: notes || null })
      navigate('/patient/matching', { state: { clinicalProfileId: profile.id, concernCategory: profile.concern_category } })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-3xl text-ink">Review Before Sharing</h1>
      <p className="mt-2 text-ink-soft">Your healthcare professional will receive the information shown here.</p>

      <Card className="mt-6 space-y-4">
        <Field label="Concern" value={structured.concern_category} />
        <Field label="Symptoms" value={structured.symptoms} />
        <Field label="Duration" value={structured.duration} />
        <Field label="Relevant medical history" value={structured.medical_history} />
        <Field label="Medications" value={structured.medications} />
        <Field label="Allergies" value={structured.allergies} />
        {structured.summary && (
          <div>
            <p className="text-xs uppercase tracking-wide text-ink-faint">AI-generated summary</p>
            <p className="mt-1 text-sm text-ink-soft">{structured.summary}</p>
          </div>
        )}
        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-ink-faint">Additional information (optional)</label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full resize-none rounded-lg border border-sage-200 bg-white px-3 py-2 text-sm outline-none focus:border-teal-500"
          />
        </div>
      </Card>

      <Card className="mt-4">
        <button
          type="button"
          onClick={() => setIdentityOpen((o) => !o)}
          className="flex w-full items-center justify-between text-left"
        >
          <span className="font-medium text-ink">Identity verification</span>
          {identityOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        {identityOpen && (
          <p className="mt-3 text-sm text-ink-soft">
            Required identity information is securely handled separately and may be accessed by an authorized
            healthcare professional when required for care.
          </p>
        )}
      </Card>

      {error && <p className="mt-4 text-sm text-clay-600">{error}</p>}

      <div className="mt-6 flex justify-end">
        <Button onClick={handleConfirm} disabled={loading}>
          {loading ? 'Confirming…' : 'Confirm & Continue'}
        </Button>
      </div>
    </div>
  )
}
