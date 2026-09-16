import Card from '../components/Card'
import Disclaimer from '../components/Disclaimer'

const steps = [
  { title: 'Create an account', body: 'Register as a patient in a couple of minutes. Basic identity details are required for compliant care — CareConfide is private, not anonymous.' },
  { title: 'Describe your concern', body: 'From your dashboard, start a new consultation and describe what you\u2019re experiencing in your own words.' },
  { title: 'AI-assisted intake', body: 'An AI intake assistant asks relevant follow-up questions and structures your answers into a clear summary. It never diagnoses.' },
  { title: 'Review before sharing', body: 'You see the exact structured summary that would be shared, and confirm it yourself before moving forward.' },
  { title: 'Find a professional', body: 'Filter by specialty, language, and consultation mode to find someone suited to your concern.' },
  { title: 'Consult', body: 'Continue the conversation with your matched professional, who sees your clinical summary and, only if you\u2019ve consented, your identity.' },
]

export default function HowItWorks() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-display text-4xl text-ink">How CareConfide Works</h1>
      <p className="mt-4 text-ink-soft">
        A step-by-step look at the path from describing a concern to speaking with a professional.
      </p>

      <div className="mt-10 space-y-6">
        {steps.map((step, i) => (
          <Card key={step.title} className="flex gap-5">
            <span className="font-display text-2xl text-teal-500">{i + 1}</span>
            <div>
              <h3 className="font-medium text-ink">{step.title}</h3>
              <p className="mt-1 text-sm text-ink-soft">{step.body}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="mt-10">
        <Disclaimer>
          CareConfide is a hackathon prototype for demonstration purposes. It does not provide medical diagnosis,
          prescriptions, or emergency care. In a medical emergency, contact local emergency services directly.
        </Disclaimer>
      </div>
    </div>
  )
}
