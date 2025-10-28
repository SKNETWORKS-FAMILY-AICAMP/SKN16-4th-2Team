import { useRef, useMemo } from 'react'
import { usePersonaStore } from '../store/usePersonaStore'
import { getRpmAvatarUrl } from '../lib/rpm/rpmHelper'

interface CustomerAvatarProps {
  className?: string
}

/**
 * 고객 아바타 표시 컴포넌트
 * 페르소나에 맞는 RPM 아바타를 로드하고 표시
 */
export default function CustomerAvatar({ className = '' }: CustomerAvatarProps) {
  const { persona, currentAudio } = usePersonaStore()
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // 페르소나가 없으면 표시하지 않음
  if (!persona) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`}>
        <p className="text-gray-500">고객 아바타가 준비되지 않았습니다.</p>
      </div>
    )
  }

  const avatarUrl = getRpmAvatarUrl(persona)

  // 오디오 재생
  const handlePlayAudio = () => {
    if (!currentAudio?.audioUrl) return

    if (audioRef.current) {
      audioRef.current.pause()
    }

    const audio = new Audio(currentAudio.audioUrl)
    audioRef.current = audio
    audio.play().catch(e => console.error('오디오 재생 실패:', e))
  }

  return (
    <div className={`relative bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* 아바타 이미지/모델 영역 */}
      <div className="aspect-square bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
        {/* TODO: RPM GLB 로드 및 렌더링 */}
        <div className="text-center">
          <div className="text-6xl mb-4">
            {persona.gender === 'female' ? '👩' : '👨'}
          </div>
          <p className="text-sm text-gray-600">{persona.type}</p>
          <p className="text-xs text-gray-500">{persona.age_group}</p>
        </div>

        {/* 임시: iframe으로 RPM 아바타 표시 */}
        {avatarUrl && (
          <iframe
            src={avatarUrl}
            className="w-full h-full border-0"
            title="Customer Avatar"
          />
        )}
      </div>

      {/* 컨트롤 패널 */}
      {currentAudio && (
        <div className="absolute bottom-4 left-4 right-4 space-y-2">
          <div className="bg-white bg-opacity-90 rounded-lg p-3 shadow">
            <p className="text-sm text-gray-700 mb-2 truncate">
              {currentAudio.text}
            </p>
            <button
              onClick={handlePlayAudio}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              🔊 다시 듣기
            </button>
          </div>
        </div>
      )}

      {/* 숨은 오디오 요소 */}
      <audio ref={audioRef} />
    </div>
  )
}

