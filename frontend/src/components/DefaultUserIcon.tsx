// DefaultUserIcon.tsx
// 사용자 기본 프로필 아이콘 (SVG)

export default function DefaultUserIcon({ className = "w-16 h-16 text-gray-400" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 97 108" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="48.5" cy="54" r="48.5" fill="#F3F4F6"/>
      <circle cx="48.5" cy="44" r="20" fill="#D1D5DB"/>
      <ellipse cx="48.5" cy="82.5" rx="28.5" ry="16.5" fill="#D1D5DB"/>
      <circle cx="48.5" cy="44" r="16" fill="#F3F4F6"/>
      <ellipse cx="48.5" cy="82.5" rx="22.5" ry="13.5" fill="#F3F4F6"/>
    </svg>
  )
}
