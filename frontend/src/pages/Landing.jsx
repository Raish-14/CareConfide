import { Link } from 'react-router-dom'
import { MessageCircle, Layers, UserCheck, SlidersHorizontal } from 'lucide-react'
import Button from '../components/Button'
import Card from '../components/Card'
import VeilMotif from '../components/VeilMotif'

const whyPoints = [
  {
    icon: Layers,
    title: 'Minimum necessary exposure',
    body: 'Your identity and your clinical information are kept apart from the start, so a professional sees what they need for care — not more.',
  },
  {
    icon: MessageCircle,
    title: 'Say it in your own words',
    body: 'An AI intake assistant helps you describe what you\u2019re experiencing, asks clarifying questions, and organizes it clearly — before anyone else sees it.',
  },
  {
    icon: UserCheck,
    title: 'You decide what\u2019s shared',
    body: 'Review every detail before it reaches a professional, and control identity access separately from clinical access.',
  },
]

const steps = [
  { title: 'Describe your concern', body: 'Tell CareConfide what\u2019s going on, in plain language.' },
  { title: 'AI-assisted intake', body: 'The assistant asks a few relevant follow-up questions and organizes your answers.' },
  { title: 'Review before sharing', body: 'You see exactly what will be shared, and confirm it yourself.' },
  { title: 'Talk to a professional', body: 'Match with a professional suited to your concern and continue the conversation.' },
]

export default function Landing() {
  return (
    <div>
      {/* Hero */}
      <section className="relative mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 overflow-hidden px-6 pb-20 pt-10 md:grid-cols-2 md:pt-16">
        <div>
          <h1 className="font-display text-5xl leading-[1.05] text-ink md:text-6xl">
            Talk Freely.
            <br />
            Heal Confidently.
          </h1>
          <p className="mt-6 max-w-md text-lg text-ink-soft">
            A privacy-first healthcare experience designed to make sensitive health conversations easier, clearer and more comfortable.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link to="/register"><Button>Start Your Journey</Button></Link>
            <Link to="/how-it-works"><Button variant="ghost">See how it works</Button></Link>
          </div>
        </div>
        <div className="relative flex justify-center">
          <VeilMotif className="w-full max-w-sm" />
        </div>
      </section>

      {/* Why CareConfide */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="font-display text-3xl text-ink">Why CareConfide</h2>
        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          {whyPoints.map(({ icon: Icon, title, body }) => (
            <Card key={title}>
              <Icon className="text-teal-500" size={28} strokeWidth={1.5} />
              <h3 className="mt-4 text-lg font-medium text-ink">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{body}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-sage-200 bg-white/40 py-16">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-3xl text-ink">How It Works</h2>
          <ol className="mt-10 grid grid-cols-1 gap-8 md:grid-cols-4">
            {steps.map((step, i) => (
              <li key={step.title} className="relative border-t border-sage-200 pt-4">
                <span className="font-display text-2xl text-teal-500">{i + 1}</span>
                <h3 className="mt-2 font-medium text-ink">{step.title}</h3>
                <p className="mt-2 text-sm text-ink-soft">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Privacy by Design */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-2 md:items-center">
          <div>
            <h2 className="font-display text-3xl text-ink">Privacy by Design</h2>
            <p className="mt-4 max-w-md text-ink-soft">
              CareConfide separates who you are from what you\u2019re experiencing. Identity information lives apart from your
              clinical profile, and a professional only sees it if it\u2019s required for your care and you\u2019ve agreed to share it.
            </p>
            <p className="mt-4 max-w-md text-sm text-ink-faint">
              CareConfide is a privacy-first platform, not an anonymous one. Verified identity remains necessary for compliant,
              professional healthcare.
            </p>
          </div>
          <Card>
            <SlidersHorizontal className="text-clay-500" size={24} strokeWidth={1.5} />
            <h3 className="mt-4 font-medium text-ink">Patient Control</h3>
            <ul className="mt-3 space-y-2 text-sm text-ink-soft">
              <li>— Review your structured intake before it\u2019s shared</li>
              <li>— Grant or withhold identity access per consultation</li>
              <li>— See a plain audit trail of who accessed what</li>
            </ul>
          </Card>
        </div>
      </section>

      {/* Professional care */}
      <section className="border-t border-sage-200 bg-white/40 py-16">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="font-display text-3xl text-ink">Professional Care, Thoughtfully Matched</h2>
          <p className="mx-auto mt-4 max-w-xl text-ink-soft">
            Once you\u2019ve reviewed your intake, CareConfide helps you find a professional suited to your concern, language, and
            preferred way of connecting.
          </p>
          <Link to="/register" className="mt-8 inline-block"><Button>Start Your Journey</Button></Link>
        </div>
      </section>
    </div>
  )
}
