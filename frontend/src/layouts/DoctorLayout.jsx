import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutGrid, Stethoscope, UserCog, LogOut } from 'lucide-react'
import Logo from '../components/Logo'
import { useAuth } from '../hooks/useAuth'

const links = [
  { to: '/doctor/dashboard', label: 'Dashboard', icon: LayoutGrid },
  { to: '/doctor/consultations', label: 'Consultations', icon: Stethoscope },
  { to: '/doctor/profile', label: 'Profile', icon: UserCog },
]

export default function DoctorLayout() {
  const { session, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="flex min-h-screen bg-sage-50 text-ink">
      <aside className="hidden w-64 flex-col justify-between border-r border-sage-200 px-6 py-8 md:flex">
        <div>
          <Logo className="mb-2 block" />
          <p className="mb-10 text-xs uppercase tracking-wide text-ink-faint">Professional</p>
          <nav className="flex flex-col gap-1">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                    isActive ? 'bg-teal-50 text-teal-700 font-medium' : 'text-ink-soft hover:bg-sage-100'
                  }`
                }
              >
                <Icon size={18} strokeWidth={1.75} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="border-t border-sage-200 pt-4">
          <p className="mb-2 text-xs uppercase tracking-wide text-ink-faint">{session?.displayName}</p>
          <button onClick={handleLogout} className="flex items-center gap-2 text-sm text-ink-soft hover:text-clay-600">
            <LogOut size={16} /> Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 px-6 py-8 md:px-12 md:py-10">
        <Outlet />
      </main>
    </div>
  )
}
