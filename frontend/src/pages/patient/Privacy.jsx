import { useEffect, useState } from 'react'
import { ShieldCheck, Eye, Layers } from 'lucide-react'
import Card from '../../components/Card'
import Disclaimer from '../../components/Disclaimer'
import { useAuth } from '../../hooks/useAuth'
import { api } from '../../services/api'

export default function Privacy() {
  const { session } = useAuth()
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    api.getPatientProfile(session.token).then(setProfile).catch(() => {})
  }, [session.token])

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-3xl text-ink">Your Privacy</h1>
      <p className="mt-2 text-ink-soft">How CareConfide handles your information.</p>

      <div className="mt-6">
        <Disclaimer>
          CareConfide is a privacy-first platform, not an anonymous one. Verified identity remains necessary for
          compliant, professional healthcare, and this prototype does not claim untraceability.
        </Disclaimer>
      </div>

      <div className="mt-6 space-y-4">
        <Card className="flex gap-4">
          <Layers className="mt-0.5 text-teal-500" size={22} strokeWidth={1.5} />
          <div>
            <h3 className="font-medium text-ink">Identity and clinical data are separated</h3>
            <p className="mt-1 text-sm text-ink-soft">
              Your name and contact details live in a separate record from your clinical summary. A professional only
              sees your clinical information by default.
            </p>
          </div>
        </Card>
        <Card className="flex gap-4">
          <Eye className="mt-0.5 text-teal-500" size={22} strokeWidth={1.5} />
          <div>
            <h3 className="font-medium text-ink">You control identity access per consultation</h3>
            <p className="mt-1 text-sm text-ink-soft">
              During a consultation, you can choose whether to share your verified identity with that specific
              professional. You can withdraw that access at any time.
            </p>
          </div>
        </Card>
        <Card className="flex gap-4">
          <ShieldCheck className="mt-0.5 text-teal-500" size={22} strokeWidth={1.5} />
          <div>
            <h3 className="font-medium text-ink">Identity status</h3>
            <p className="mt-1 text-sm text-ink-soft">
              {profile?.identity_verified
                ? 'Your identity is verified on this demo account.'
                : 'Your identity is not yet verified on this demo account.'}
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
