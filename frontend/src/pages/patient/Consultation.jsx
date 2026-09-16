import { useEffect, useRef, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { Mic, MicOff, Video, VideoOff, PhoneOff, Send, ShieldCheck } from 'lucide-react'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { useAuth } from '../../hooks/useAuth'
import { api, ApiError } from '../../services/api'

export default function Consultation() {
  const { session } = useAuth()
  const location = useLocation()
  const consultationId = location.state?.consultationId
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [muted, setMuted] = useState(false)
  const [cameraOff, setCameraOff] = useState(true)
  const [ended, setEnded] = useState(false)
  const [identityGranted, setIdentityGranted] = useState(false)
  const [error, setError] = useState('')
  const scrollRef = useRef(null)

  useEffect(() => {
    if (!consultationId) return
    api.getConsultationMessages(session.token, consultationId).then(setMessages).catch(() => {})
  }, [consultationId, session.token])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  if (!consultationId) {
    return (
      <div className="max-w-2xl">
        <Card>
          <p className="text-ink-soft">
            No active consultation selected. <Link to="/patient/matching" className="text-teal-600 hover:underline">Find a professional</Link> to begin one.
          </p>
        </Card>
      </div>
    )
  }

  const send = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    const content = text
    setText('')
    setMessages((m) => [...m, { sender_role: 'patient', content, created_at: new Date().toISOString() }])
    try {
      await api.postConsultationMessage(session.token, consultationId, content)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Message could not be sent.')
    }
  }

  const toggleIdentityConsent = async () => {
    const granted = !identityGranted
    try {
      await api.updateConsent(session.token, { consultation_id: consultationId, scope: 'identity_data', granted })
      setIdentityGranted(granted)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update consent.')
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink">Consultation</h1>
          <p className="text-sm text-ink-soft">Simulated consultation interface — this is a hackathon demo, not real video/audio.</p>
        </div>
      </div>

      <Card className="mt-4 flex items-center justify-between bg-sage-100/60">
        <div className="flex items-center gap-2 text-sm text-ink-soft">
          <ShieldCheck size={16} className="text-teal-500" />
          Share identity with your professional?
        </div>
        <button
          onClick={toggleIdentityConsent}
          className={`rounded-full px-4 py-1.5 text-xs font-medium ${
            identityGranted ? 'bg-teal-500 text-sage-50' : 'border border-sage-200 text-ink-soft'
          }`}
        >
          {identityGranted ? 'Identity shared' : 'Identity withheld'}
        </button>
      </Card>

      <Card className="mt-4 flex h-[360px] flex-col items-center justify-center gap-3 bg-ink text-sage-50">
        {cameraOff ? (
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-ink-soft text-2xl font-display">
            {session.displayName?.[0] || 'P'}
          </div>
        ) : (
          <p className="text-sm text-sage-200">Camera placeholder — no real video in this demo</p>
        )}
        <p className="text-sm text-sage-300">{ended ? 'Call ended' : 'Connected'}</p>
      </Card>

      <div className="mt-3 flex justify-center gap-4">
        <button
          onClick={() => setMuted((m) => !m)}
          className={`flex h-11 w-11 items-center justify-center rounded-full border ${muted ? 'border-clay-500 text-clay-600' : 'border-sage-200 text-ink-soft'}`}
        >
          {muted ? <MicOff size={18} /> : <Mic size={18} />}
        </button>
        <button
          onClick={() => setCameraOff((c) => !c)}
          className={`flex h-11 w-11 items-center justify-center rounded-full border ${cameraOff ? 'border-clay-500 text-clay-600' : 'border-sage-200 text-ink-soft'}`}
        >
          {cameraOff ? <VideoOff size={18} /> : <Video size={18} />}
        </button>
        <button
          onClick={() => setEnded(true)}
          className="flex h-11 w-11 items-center justify-center rounded-full bg-clay-500 text-white"
        >
          <PhoneOff size={18} />
        </button>
      </div>

      <Card className="mt-4">
        <div ref={scrollRef} className="max-h-72 space-y-3 overflow-y-auto pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.sender_role === 'patient' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${m.sender_role === 'patient' ? 'bg-teal-500 text-sage-50' : 'bg-sage-100 text-ink'}`}>
                {m.content}
              </div>
            </div>
          ))}
          {messages.length === 0 && <p className="text-sm text-ink-faint">No messages yet.</p>}
        </div>
        {!ended && (
          <form onSubmit={send} className="mt-3 flex gap-2">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type a message…"
              className="flex-1 rounded-full border border-sage-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-teal-500"
            />
            <Button type="submit" className="px-4 py-2.5"><Send size={16} /></Button>
          </form>
        )}
        {error && <p className="mt-2 text-sm text-clay-600">{error}</p>}
      </Card>
    </div>
  )
}
