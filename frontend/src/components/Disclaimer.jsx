export default function Disclaimer({ children }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-400/40 bg-amber-100 px-4 py-3 text-sm text-ink-soft">
      <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-600" />
      <p>{children}</p>
    </div>
  )
}
