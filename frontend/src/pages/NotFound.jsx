import { Link } from 'react-router-dom'
import Button from '../components/Button'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-sage-50 px-6 text-center">
      <h1 className="font-display text-4xl text-ink">Page not found</h1>
      <p className="mt-3 text-ink-soft">The page you're looking for doesn't exist.</p>
      <Link to="/" className="mt-6"><Button>Back home</Button></Link>
    </div>
  )
}
