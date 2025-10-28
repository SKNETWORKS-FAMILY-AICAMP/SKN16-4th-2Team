/**
 * Ready Player Me 아바타 URL 생성
 * 페르소나 정보를 기반으로 RPM 아바타 URL을 생성
 */
import { Persona } from '../../store/usePersonaStore'

const RPM_BASE_URL = 'https://api.readyplayer.me/v1/avatars'

export function getRpmAvatarUrl(persona: Persona): string {
  // 실제 구현에서는:
  // 1. 페르소나별 GLB 파일을 미리 생성해 저장
  // 2. 또는 RPM Creator API로 즉시 생성
  
  // 임시: 페르소나 ID 기반 랜덤 아바타 URL
  // 나중에 실제 GLB 파일 경로로 교체
  
  const gender = persona.gender === 'female' ? 'female' : 'male'
  const agePrefix = persona.age_group.replace('s', 's') // "30s" -> "30s"
  
  // RPM은 브라우저에서 직접 GLB URL을 로드 가능
  // 예: https://models.readyplayer.me/avatar-id.glb
  
  // 임시로 기본 RPM 아바타 사용
  return ''
}

/**
 * 페르소나별 아바타 프리셋
 */
export const PERSONA_AVATARS: Record<string, string> = {
  'p_20s_student_lowlit_practical_f': 'https://models.readyplayer.me/avatar1.glb',
  'p_20s_student_lowlit_practical_m': 'https://models.readyplayer.me/avatar2.glb',
  'p_30s_officeworker_lowlit_conservative_f': 'https://models.readyplayer.me/avatar3.glb',
  'p_40s_retired_lowlit_impatient_m': 'https://models.readyplayer.me/avatar4.glb',
  // ... 더 많은 페르소나 추가
}

export function getPersonaAvatarUrl(personaId: string): string {
  return PERSONA_AVATARS[personaId] || ''
}

