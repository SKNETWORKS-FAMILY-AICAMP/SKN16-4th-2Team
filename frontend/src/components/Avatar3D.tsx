import { useRef, useFrame, useEffect } from 'react'
import { Canvas, useLoader } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { usePersonaStore } from '../store/usePersonaStore'
import { VISEME_TO_MORPH } from '../lib/lipsync/visemeMap'

interface Avatar3DProps {
  avatarUrl: string
}

/**
 * 3D 아바타 컴포넌트 (Ready Player Me GLB)
 * Rhubarb mouthCues 기반 립싱크 애니메이션
 */
function Avatar3DModel({ avatarUrl }: Avatar3DProps) {
  const { currentAudio } = usePersonaStore()
  const groupRef = useRef<THREE.Group>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  
  // GLB 로드
  const gltf = useLoader(GLTFLoader, avatarUrl)
  const scene = gltf.scene

  // 오디오 재생
  useEffect(() => {
    if (!currentAudio?.audioUrl) return

    const audio = new Audio(currentAudio.audioUrl)
    audioRef.current = audio
    
    audio.play().catch(e => {
      console.error('아바타 오디오 재생 실패:', e)
    })

    return () => {
      audio.pause()
      audioRef.current = null
    }
  }, [currentAudio?.audioUrl])

  // 립싱크 애니메이션
  useFrame(() => {
    if (!groupRef.current || !audioRef.current || !currentAudio?.mouthCues) return

    const currentTime = audioRef.current.currentTime

    // 현재 시간에 해당하는 mouthCue 찾기
    const activeCue = currentAudio.mouthCues.find(
      cue => currentTime >= cue.start && currentTime <= cue.end
    )

    // 모든 morph target 초기화
    scene.traverse((child: any) => {
      if (child.isMesh && child.morphTargetInfluences) {
        // 기본적으로 모든 morph 0으로
        child.morphTargetInfluences.fill(0)

        // activeCue가 있으면 해당 viseme 적용
        if (activeCue) {
          const morphConfig = VISEME_TO_MORPH[activeCue.value]
          
          if (morphConfig && child.morphTargetDictionary) {
            const morphIndex = child.morphTargetDictionary[morphConfig.key]
            if (morphIndex !== undefined && child.morphTargetInfluences[morphIndex] !== undefined) {
              child.morphTargetInfluences[morphIndex] = morphConfig.weight
            }
          }
        }
      }
    })
  })

  // 디버그: morph target 이름들 출력
  useEffect(() => {
    scene.traverse((child: any) => {
      if (child.isMesh && child.morphTargetDictionary) {
        console.log('📋 Morph Targets:', child.name, child.morphTargetDictionary)
      }
    })
  }, [scene])

  return (
    <primitive 
      ref={groupRef} 
      object={scene} 
      position={[0, -1.5, 0]} 
      scale={[1, 1, 1]}
    />
  )
}

/**
 * 3D 캔버스 래퍼
 */
export default function Avatar3D({ avatarUrl }: Avatar3DProps) {
  // avatarUrl이 없으면 표시 안함
  if (!avatarUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded-lg">
        <p className="text-gray-500">3D 아바타를 로드할 수 없습니다.</p>
      </div>
    )
  }

  return (
    <Canvas camera={{ position: [0, 1.5, 3], fov: 50 }}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[2, 4, 3]} intensity={0.8} />
      <pointLight position={[-2, -1, 2]} intensity={0.5} />
      
      {/* 3D 모델 */}
      <Avatar3DModel avatarUrl={avatarUrl} />

      {/* OrbitControls로 카메라 제어 */}
      <OrbitControls
        enablePan={false}
        minDistance={2}
        maxDistance={5}
        minPolarAngle={Math.PI / 6}
        maxPolarAngle={Math.PI / 2}
      />

      {/* 환경 배경 */}
      <Environment preset="dawn" />
    </Canvas>
  )
}

