import { useEffect, useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { Globe2, Video, MessageCircle, Clock } from 'lucide-react'
import Card from '../../components/Card'
import Button from '../../components/Button'
import { useAuth } from '../../hooks/useAuth'
import { api, ApiError } from '../../services/api'

export default function Matching() {
  const { session } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { clinicalProfileId, concernCategory } = location.state || {}

  const [professionals, setProfessionals] = useState([])
  const [filters, setFilters] = useState({ specialty: '', language: '', mode: '' })
  const [error, setError] = useState('')
  const [requestingId, setRequestingId] = useState(null)

  const load = async (f = filters) => {
    try {
      const res = await api.listProfessionals(session.token, f)
      setProfessionals(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not load professionals.')
    }
  }

  useEffect(() => {
    load({ specialty: concernCategory || '' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const applyFilters = (e) => {
    e.preventDefault()
    load(filters)
  }

  const requestConsultation = async (professionalId, mode) => {
    if (!clinicalProfileId) {
      setError('Please complete and confirm an intake before requesting a consultation.')
      return
    }
    setRequestingId(professionalId)
    setError('')
    try {
      const consult = await api.createConsultation(session.token, {
        professional_id: professionalId,
        clinical_profile_id: clinicalProfileId,
        mode,
      })
      navigate('/patient/consultation', { state: { consultationId: consult.id } })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not request a consultation.')
    } finally {
      setRequestingId(null)
    }
  }

  return (
    <div className="max-w-4xl">
      <h1 className="font-display text-3xl text-ink">Find a Healthcare Professional</h1>
      <p className="mt-2 text-ink-soft">Choose someone suited to your concern, language, and preferred way of connecting.</p>

      {!clinicalProfileId && (
        <p className="mt-3 text-sm text-clay-600">
          You haven't confirmed an intake yet. <Link to="/patient/intake" className="underline">Start one first</Link>, or continue browsing.
        </p>
      )}

      <form onSubmit={applyFilters} className="mt-6 flex flex-wrap gap-3">
        <input
          placeholder="Specialty"
          value={filters.specialty}
          onChange={(e) => setFilters((f) => ({ ...f, specialty: e.target.value }))}
          className="rounded-full border border-sage-200 bg-white px-4 py-2 text-sm outline-none focus:border-teal-500"
        />
        <input
          placeholder="Language"
          value={filters.language}
          onChange={(e) => setFilters((f) => ({ ...f, language: e.target.value }))}
          className="rounded-full border border-sage-200 bg-white px-4 py-2 text-sm outline-none focus:border-teal-500"
        />
        <select
          value={filters.mode}
          onChange={(e) => setFilters((f) => ({ ...f, mode: e.target.value }))}
          className="rounded-full border border-sage-200 bg-white px-4 py-2 text-sm outline-none focus:border-teal-500"
        >
          <option value="">Any mode</option>
          <option value="chat">Chat</option>
          <option value="video">Video</option>
          <option value="audio">Audio</option>
        </select>
        <Button type="submit" variant="secondary" className="px-5 py-2 text-sm">Filter</Button>
      </form>

      {error && <p className="mt-4 text-sm text-clay-600">{error}</p>}

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
        {professionals.map((p) => (
          <Card key={p.id}>
            <h3 className="font-medium text-ink">{p.full_name}</h3>
            <p className="text-sm text-teal-600">{p.specialty}</p>
            {p.bio && <p className="mt-2 text-sm text-ink-soft">{p.bio}</p>}
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-ink-faint">
              <span className="flex items-center gap-1"><Globe2 size={14} /> {p.languages.join(', ')}</span>
              <span className="flex items-center gap-1"><Clock size={14} /> {p.availability}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {p.consultation_modes.map((mode) => (
                <Button
                  key={mode}
                  variant="secondary"
                  className="px-4 py-1.5 text-xs capitalize"
                  disabled={requestingId === p.id}
                  onClick={() => requestConsultation(p.id, mode)}
                >
                  {mode === 'video' ? <Video size={14} /> : <MessageCircle size={14} />}
                  Request {mode}
                </Button>
              ))}
            </div>
          </Card>
        ))}
        {professionals.length === 0 && (
          <p className="text-sm text-ink-soft">No professionals match those filters.</p>
        )}
      </div>
    </div>
  )
}
