export default function Card({ children, className = '' }) {
  return (
    <div className={`rounded-xl2 border border-sage-200 bg-white/70 p-6 shadow-quiet ${className}`}>
      {children}
    </div>
  )
}
