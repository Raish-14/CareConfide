import { Link, Outlet } from 'react-router-dom'
import Logo from '../components/Logo'
import Button from '../components/Button'
import { useAuth } from '../hooks/useAuth'

export default function PublicLayout() {
  const { session } = useAuth()
  const dashboardPath = session?.role === 'professional' ? '/doctor/dashboard' : '/patient/dashboard'

  return (
    <div className="min-h-screen bg-sage-50 text-ink">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Link to="/"><Logo /></Link>
        <nav className="hidden items-center gap-8 text-sm text-ink-soft md:flex">
          <Link to="/how-it-works" className="hover:text-teal-600">How It Works</Link>
          <Link to="/patient/privacy" className="hover:text-teal-600">Privacy</Link>
          <Link to="/register?role=professional" className="hover:text-teal-600">For Professionals</Link>
        </nav>
        <div className="flex items-center gap-3">
          {session ? (
            <Link to={dashboardPath}>
              <Button variant="secondary" className="px-5 py-2 text-sm">Go to dashboard</Button>
            </Link>
          ) : (
            <>
              <Link to="/login" className="hidden text-sm text-ink-soft hover:text-teal-600 sm:inline">Log in</Link>
              <Link to="/register">
                <Button className="px-5 py-2 text-sm">Get Started</Button>
              </Link>
            </>
          )}
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="border-t border-sage-200 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 text-sm text-ink-faint sm:flex-row">
          <Logo className="text-base" />
          <p>CareConfide is a demonstration prototype. Not for real medical use.</p>
        </div>
      </footer>
    </div>
  )
}
