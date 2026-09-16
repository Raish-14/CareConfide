export default function Button({ children, variant = 'primary', className = '', ...props }) {
  const base = 'inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-[15px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-teal-500 text-sage-50 hover:bg-teal-600',
    secondary: 'bg-transparent border border-ink/20 text-ink hover:border-teal-500 hover:text-teal-600',
    ghost: 'bg-transparent text-ink-soft hover:text-teal-600',
    danger: 'bg-transparent border border-clay-500/50 text-clay-600 hover:bg-clay-500/10',
  }
  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  )
}
