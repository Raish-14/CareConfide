import Card from '../../components/Card'
import { useAuth } from '../../hooks/useAuth'

export default function DoctorProfile() {
  const { session } = useAuth()

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-3xl text-ink">Profile</h1>
      <p className="mt-2 text-ink-soft">Your professional details as shown to patients during matching.</p>

      <Card className="mt-6 space-y-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint">Name</p>
          <p className="mt-1 text-sm text-ink">{session.displayName}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-ink-faint">Role</p>
          <p className="mt-1 text-sm capitalize text-ink">{session.role}</p>
        </div>
        <p className="text-xs text-ink-faint">
          In this prototype, profile editing (specialty, languages, availability) is managed via the demo seed data.
        </p>
      </Card>
    </div>
  )
}
