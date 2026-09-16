import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send } from 'lucide-react'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Disclaimer from '../../components/Disclaimer'
import { useAuth } from '../../hooks/useAuth'
import { api, ApiError } from '../../services/api'

export default function Intake() {
  const { session } = useAuth()
  const navigate = useNavigate()

  const [description, setDescription] = useState('')
  const [started, setStarted] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([]) // {sender, content}
  const [structured, setStructured] = useState(null)
  const [aiMode, setAiMode] = useState(null)
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleStart = async (e) => {
    e.preventDefault()
    if (!description.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await api.startIntake(session.token, description)
      setSessionId(res.session_id)
      setAiMode(res.ai_mode)
      setStructured(res.structured)
      setMessages([
        { sender: 'patient', content: description },
        { sender: 'ai', content: res.structured.follow_up_question || res.structured.summary },
      ])
      setStarted(true)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReply = async (e) => {
    e.preventDefault()
    if (!reply.trim()) return
    setLoading(true)
    setError('')
    const patientMsg = { sender: 'patient', content: reply }
    setMessages((m) => [...m, patientMsg])
    setReply('')
    try {
      const res = await api.replyIntake(session.token, sessionId, patientMsg.content)
      setAiMode(res.ai_mode)
      setStructured(res.structured)
      setMessages((m) => [...m, { sender: 'ai', content: res.structured.follow_up_question || res.structured.summary }])
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const goToReview = () => {
    navigate('/patient/review', { state: { sessionId, structured } })
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-3xl text-ink">Tell us what's bothering you</h1>
      <p className="mt-2 text-ink-soft">
        Describe what you're experiencing in your own words. You don't need to know the medical terminology.
      </p>

      <div className="mt-4">
        <Disclaimer>AI-assisted intake — not a medical diagnosis.</Disclaimer>
      </div>

      {!started ? (
        <form onSubmit={handleStart} className="mt-6">
          <Card>
            <textarea
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="For example: I've noticed a change I'm worried about and I'm not sure what it means…"
              className="w-full resize-none rounded-lg border border-sage-200 bg-white px-4 py-3 text-sm outline-none focus:border-teal-500"
            />
            {error && <p className="mt-2 text-sm text-clay-600">{error}</p>}
            <div className="mt-4 flex justify-end">
              <Button type="submit" disabled={loading}>{loading ? 'Starting…' : 'Continue'}</Button>
            </div>
          </Card>
        </form>
      ) : (
        <div className="mt-6 space-y-4">
          {aiMode === 'demo' && (
            <p className="text-xs uppercase tracking-wide text-clay-600">Demo AI mode — live AI credentials not configured</p>
          )}
          <Card className="space-y-4">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.sender === 'patient' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                    m.sender === 'patient' ? 'bg-teal-500 text-sage-50' : 'bg-sage-100 text-ink'
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
          </Card>

          {structured?.ready_for_review ? (
            <Card className="bg-teal-50/60">
              <p className="text-sm text-ink-soft">
                We have enough information to prepare a summary for review.
              </p>
              <div className="mt-3 flex justify-end">
                <Button onClick={goToReview}>Review my information</Button>
              </div>
            </Card>
          ) : (
            <form onSubmit={handleReply} className="flex gap-2">
              <input
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder="Type your reply…"
                className="flex-1 rounded-full border border-sage-200 bg-white px-5 py-3 text-sm outline-none focus:border-teal-500"
              />
              <Button type="submit" disabled={loading} className="px-4">
                <Send size={18} />
              </Button>
            </form>
          )}
          {error && <p className="text-sm text-clay-600">{error}</p>}
        </div>
      )}
    </div>
  )
}
