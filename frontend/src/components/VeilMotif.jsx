// A soft, layered-blob motif used as the hero's visual anchor: overlapping
// translucent forms suggest a conversation held gently behind a veil,
// without resorting to padlock/shield clip-art clichés.
export default function VeilMotif({ className = '' }) {
  return (
    <svg viewBox="0 0 480 480" className={className} xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="240" cy="240" r="200" fill="#EAF2EF" />
      <ellipse cx="190" cy="200" rx="130" ry="110" fill="#CFE3DC" opacity="0.8" />
      <ellipse cx="290" cy="290" rx="110" ry="95" fill="#D9A08F" opacity="0.35" />
      <circle cx="240" cy="240" r="60" fill="#2F6F62" opacity="0.9" />
      <circle cx="222" cy="228" r="6" fill="#F6F5F1" />
      <circle cx="258" cy="228" r="6" fill="#F6F5F1" />
      <path d="M215 258 Q240 272 265 258" stroke="#F6F5F1" strokeWidth="4" strokeLinecap="round" fill="none" />
    </svg>
  )
}
