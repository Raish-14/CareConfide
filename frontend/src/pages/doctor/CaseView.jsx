import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ChevronDown, ChevronUp, Send } from 'lucide-react'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Disclaimer from '../../components/Disclaimer'
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

export default function DoctorCase() {
  const { id } = useParams()
  const { session } = useAuth()
  const [caseData, setCaseData] = useState(null)
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [identityOpen, setIdentityOpen] = useState(false)
  const [error, setError] = useState('')
  const scrollRef = useRef(null)

  const load = () => {
    api.getDoctorCase(session.token, id).then(setCaseData).catch((e) => setError(e.message))
    api.getConsultationMessages(session.token, id).then(setMessages).catch(() => {})
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  if (error) {
    return <p className="text-sm text-clay-600">{error}</p>
  }
  if (!caseData) {
    return <p className="text-sm text-ink-soft">Loading case…</p>
  }

  const send = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    const content = text
    setText('')
    setMessages((m) => [...m, { sender_role: 'professional', content, created_at: new Date().toISOString() }])
    try {
      await api.postConsultationMessage(session.token, id, content)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Message could not be sent.')
    }
  }

  const profile = caseData.clinical_profile

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-2xl text-ink">Case: {caseData.patient_display_id}</h1>
      <span className="mt-1 inline-block rounded-full bg-sage-100 px-3 py-1 text-xs capitalize text-ink-soft">{caseData.status}</span>

      <div className="mt-4">
        <Disclaimer>AI-generated intake summary. This is not a diagnosis.</Disclaimer>
      </div>

      <Card className="mt-4 space-y-4">
        <h2 className="font-medium text-ink">AI-Assisted Intake Summary</h2>
        {profile ? (
          <>
            <Field label="Concern" value={profile.concern_category} />
            <Field label="Symptoms" value={profile.symptoms} />
            <Field label="Duration" value={profile.duration} />
            <Field label="Medical history" value={profile.medical_history} />
            <Field label="Medications" value={profile.medications} />
            <Field label="Allergies" value={profile.allergies} />
            <Field label="Additional notes" value={profile.additional_notes} />
            {profile.ai_summary && (
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-faint">Summary</p>
                <p className="mt-1 text-sm text-ink-soft">{profile.ai_summary}</p>
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-ink-soft">No clinical profile on file for this case.</p>
        )}
      </Card>

      <Card className="mt-4">
        <button
          type="button"
          onClick={() => setIdentityOpen((o) => !o)}
          className="flex w-full items-center justify-between text-left"
        >
          <span className="font-medium text-ink">Authorized Identity Information</span>
          {identityOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        {identityOpen && (
          <div className="mt-3 text-sm text-ink-soft">
            {caseData.identity_access_granted && caseData.identity ? (
              <div className="space-y-1">
                <p><span className="text-ink-faint">Name:</span> {caseData.identity.full_name}</p>
                <p><span className="text-ink-faint">Date of birth:</span> {caseData.identity.date_of_birth || 'Not provided'}</p>
                <p><span className="text-ink-faint">Phone:</span> {caseData.identity.phone || 'Not provided'}</p>
                <p><span className="text-ink-faint">Verified:</span> {caseData.identity.identity_verified ? 'Yes' : 'No'}</p>
              </div>
            ) : (
              <p>The patient has not authorized identity access for this consultation yet.</p>
            )}
          </div>
        )}
      </Card>

      <Card className="mt-4">
        <h2 className="mb-3 font-medium text-ink">Consultation</h2>
        <div ref={scrollRef} className="max-h-64 space-y-3 overflow-y-auto pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.sender_role === 'professional' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${m.sender_role === 'professional' ? 'bg-teal-500 text-sage-50' : 'bg-sage-100 text-ink'}`}>
                {m.content}
              </div>
            </div>
          ))}
          {messages.length === 0 && <p className="text-sm text-ink-faint">No messages yet.</p>}
        </div>
        <form onSubmit={send} className="mt-3 flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type a message…"
            className="flex-1 rounded-full border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
          />
          <Button type="submit" className="px-4 py-2.5"><Send size={16} /></Button>
        </form>
      </Card>
    </div>
  )
}
