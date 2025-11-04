import React, { useState, useRef, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { usePersonaStore } from '../store/usePersonaStore'
import api from '../utils/api'
import { ragSimulationAPI } from '../utils/api'
import { playFromAnyAudioPayload } from '../utils/audio'
import { AudioVisualizer } from '../components/AudioVisualizer'
import CustomerAvatar from '../components/CustomerAvatar'
import {
  MicrophoneIcon,
  StopIcon,
  PlayIcon,
  SpeakerWaveIcon,
  ArrowPathIcon,
  ArrowLeftIcon,
  VideoCameraIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  CheckIcon
} from '@heroicons/react/24/outline'

interface VoiceSimulationProps {
  simulationData: any
  onBack: () => void
}

// 대화 메시지 타입
interface ChatMessage {
  id: string
  role: 'user' | 'customer'
  text: string
  audio?: string
  timestamp: Date
}

const VoiceSimulation: React.FC<VoiceSimulationProps> = ({ simulationData, onBack }) => {
  const { user } = useAuthStore()
  const { setPersona, setAudio } = usePersonaStore()
  const [isRecording, setIsRecording] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [userMessage, setUserMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]) // 대화 히스토리
  const [subtitle, setSubtitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [stream, setStream] = useState<MediaStream | null>(null) // 오디오 스트림
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null) // 비디오 스트림
  const [isInitializing, setIsInitializing] = useState(true) // 초기화 상태
  const [isStarted, setIsStarted] = useState(false) // 시뮬레이션 시작 여부
  const [isCustomerInfoOpen, setIsCustomerInfoOpen] = useState(false) // 고객 정보 접기/펼치기 (기본값: 접힘)
  const [isSituationInfoOpen, setIsSituationInfoOpen] = useState(false) // 상황 정보 접기/펼치기 (기본값: 접힘)
  const [checkedGoals, setCheckedGoals] = useState<Set<number>>(new Set()) // 달성된 목표 인덱스
  const [isSimulationCompleted, setIsSimulationCompleted] = useState(false) // 시뮬레이션 완료 상태

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const videoRecorderRef = useRef<MediaRecorder | null>(null) // 화면 녹화용
  const videoChunksRef = useRef<Blob[]>([]) // 화면 녹화 데이터
  const audioRef = useRef<HTMLAudioElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null) // 스크롤 자동 이동용
  const videoRef = useRef<HTMLVideoElement>(null) // 비디오 엘리먼트 참조

  // 카메라 스트림 초기화
  useEffect(() => {
    if (isStarted) {
      const initCamera = async () => {
        try {
          console.log('🎥 카메라 초기화 시작...')
          const stream = await navigator.mediaDevices.getUserMedia({ 
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              facingMode: 'user'
            },
            audio: false // 비디오만 가져오기 (오디오는 별도로)
          })
          console.log('✅ 카메라 스트림 획득 성공:', stream)
          setVideoStream(stream)
          
          // 스트림을 비디오 엘리먼트에 할당
          if (videoRef.current) {
            videoRef.current.srcObject = stream
            videoRef.current.play().catch(err => {
              console.error('비디오 재생 실패:', err)
            })
            console.log('✅ 비디오 엘리먼트에 스트림 할당 완료')
          } else {
            console.warn('⚠️ videoRef.current가 null입니다')
          }
        } catch (error: any) {
          console.error('❌ 카메라 접근 실패:', error)
          setError(`카메라 접근 권한이 필요합니다: ${error.message}`)
        }
      }
      initCamera()
    }

    // 컴포넌트 언마운트 시 정리
    return () => {
      if (videoStream) {
        console.log('🧹 카메라 스트림 정리 중...')
        videoStream.getTracks().forEach(track => {
          track.stop()
          console.log('✅ 트랙 정리 완료:', track.kind)
        })
        setVideoStream(null)
      }
    }
  }, [isStarted])

  // videoStream이 변경될 때 비디오 엘리먼트 업데이트
  useEffect(() => {
    if (videoStream && videoRef.current) {
      console.log('🔄 비디오 스트림 업데이트 중...')
      videoRef.current.srcObject = videoStream
      videoRef.current.play().catch(err => {
        console.error('비디오 재생 실패:', err)
      })
    }
  }, [videoStream])

  // 페르소나 설정 및 (시작 버튼 이후) 초기 멘트 처리
  useEffect(() => {
    if (!isStarted) return
    if (simulationData?.persona) {
      setPersona({
        persona_id: simulationData.persona.id || '',
        avatarUrl: '', // TODO: RPM URL
        voicePreset: simulationData.persona.type || '',
        gender: simulationData.persona.gender || 'male',
        age_group: simulationData.persona.age_group || '',
        type: simulationData.persona.type || ''
      })

      // 🔥 초기 메시지가 있으면 아바타가 말하도록 설정
      if (simulationData?.initial_message?.audio_url) {
        setAudio({
          audioUrl: simulationData.initial_message.audio_url,
          text: simulationData.initial_message.content || '',
          mouthCues: []
        })
        
        // 초기 메시지를 대화 히스토리에 추가
        const initialMessage: ChatMessage = {
          id: `initial_${Date.now()}`,
          role: 'customer',
          text: simulationData.initial_message.content || '',
          audio: simulationData.initial_message.audio_url,
          timestamp: new Date()
        }
        
        setChatHistory([initialMessage])
        
        // 초기 메시지 자동 재생
        setTimeout(() => {
          playFromAnyAudioPayload(simulationData.initial_message.audio_url, 'audio/mpeg')
          setIsInitializing(false) // 초기화 완료
        }, 500)
      } else {
        setIsInitializing(false) // 초기 메시지가 없어도 초기화 완료
      }
    }
  }, [simulationData, isStarted])

  // 새 메시지 추가 시 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  // 대화 종료 표현 감지
  const checkConversationEnd = (message: string): boolean => {
    const endKeywords = [
      '감사합니다',
      '수고하셨습니다',
      '감사해요',
      '고마워요',
      '고맙습니다',
      '끝',
      '종료',
      '마무리',
      '그럼 이만',
      '안녕히가세요',
      '수고하세요'
    ]
    
    const lowerMessage = message.toLowerCase().trim()
    return endKeywords.some(keyword => lowerMessage.includes(keyword.toLowerCase()))
  }

  // 시뮬레이션 종료 처리
  const handleEndSimulation = async () => {
    console.log('🔚 시뮬레이션 종료 처리 시작...')
    
    try {
      // 화면 녹화 중지 및 업로드
      if (videoRecorderRef.current && videoRecorderRef.current.state !== 'inactive') {
        console.log('📹 화면 녹화 중지 및 업로드 중...')
        videoRecorderRef.current.stop()
        
        videoRecorderRef.current.onstop = async () => {
          // 녹화 데이터를 Blob으로 변환
          const videoBlob = new Blob(videoChunksRef.current, { type: 'video/webm' })
          console.log('✅ 녹화 완료, 파일 크기:', videoBlob.size, 'bytes')
          
          // 녹화 파일 업로드
          if (videoBlob.size > 0) {
            await uploadRecording(videoBlob)
          }
          
          // 녹화 데이터 초기화
          videoChunksRef.current = []
          
          // 완료 상태로 변경
          setIsSimulationCompleted(true)
        }
      } else {
        // 녹화가 없으면 바로 완료 상태로 변경
        setIsSimulationCompleted(true)
      }

      // 오디오 녹화 중지
      if (isRecording && mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        console.log('🎤 오디오 녹화 중지 중...')
        mediaRecorderRef.current.stop()
        setIsRecording(false)
      }

      // 카메라 스트림 정리
      if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop())
        setVideoStream(null)
      }

      // 오디오 스트림 정리
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
        setStream(null)
      }

      console.log('✅ 시뮬레이션 종료 처리 완료')
    } catch (error) {
      console.error('❌ 시뮬레이션 종료 처리 실패:', error)
      // 오류가 발생해도 완료 페이지 표시
      setIsSimulationCompleted(true)
    }
  }
  
  // 다시 시뮬레이션 시작
  const handleRestartSimulation = () => {
    // 모든 상태 초기화
    setIsSimulationCompleted(false)
    setChatHistory([])
    setCheckedGoals(new Set())
    setIsStarted(false)
    setIsInitializing(true)
    setUserMessage('')
    setError('')
    setIsPlaying(false)
    setIsRecording(false)
    
    // 녹화 관련 초기화
    videoChunksRef.current = []
    audioChunksRef.current = []
    mediaRecorderRef.current = null
    videoRecorderRef.current = null
    
    // 스트림 정리
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop())
      setVideoStream(null)
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
      setStream(null)
    }
    
    console.log('🔄 시뮬레이션 재시작 준비 완료')
  }
  
  // 평가 페이지로 이동 (평가 페이지가 준비되면 라우팅 추가)
  const handleGoToEvaluation = () => {
    // TODO: 평가 페이지 라우팅
    // 예: navigate('/evaluation', { state: { simulationData, chatHistory, checkedGoals } })
    console.log('📝 평가 페이지로 이동 준비')
    alert('평가 페이지가 준비 중입니다. 곧 업데이트될 예정입니다.')
  }

  // 목표 달성 분석 함수
  const analyzeGoalAchievement = async (history: ChatMessage[]) => {
    const goals = simulationData?.situation?.goals
    if (!goals || goals.length === 0) {
      return
    }

    // 사용자 메시지가 있는지 확인
    const hasUserMessages = history.some(msg => msg.role === 'user')
    if (!hasUserMessages) {
      return
    }

    try {
      console.log('🎯 목표 달성 분석 시작...')
      
      // 대화 히스토리를 API 형식으로 변환
      const conversationHistory = history.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'customer',
        text: msg.text
      }))

      const result = await ragSimulationAPI.analyzeGoalAchievement(conversationHistory, goals)
      
      console.log('✅ 목표 달성 분석 결과:', result)
      
      // 달성된 목표 인덱스를 Set으로 변환
      const achievedIndicesArray = (result.achieved_goal_indices || []) as number[]
      const achievedIndices = new Set<number>(achievedIndicesArray)
      setCheckedGoals(achievedIndices)
      
    } catch (error) {
      console.error('❌ 목표 달성 분석 실패:', error)
    }
  }

  // 대화 히스토리가 변경될 때마다 목표 달성 분석 (고객 응답 후 분석)
  useEffect(() => {
    if (!isStarted || isInitializing) {
      return
    }

    const userMessages = chatHistory.filter(msg => msg.role === 'user')
    if (userMessages.length === 0) {
      return
    }

    // 마지막 메시지 확인
    const lastMessage = chatHistory[chatHistory.length - 1]
    if (lastMessage) {
      // 고객 응답이 온 후 약간의 지연을 두고 분석
      const delay = lastMessage.role === 'customer' ? 1000 : 3000
      const timer = setTimeout(() => {
        analyzeGoalAchievement(chatHistory)
      }, delay)

      return () => clearTimeout(timer)
    }
  }, [chatHistory, isStarted, isInitializing, simulationData])

  // 녹화 파일 업로드
  const uploadRecording = async (videoBlob: Blob) => {
    try {
      console.log('📤 녹화 파일 업로드 시작...')
      
      const formData = new FormData()
      formData.append('video', videoBlob, `simulation_${Date.now()}.webm`)
      formData.append('session_data', JSON.stringify({
        simulation_id: simulationData?.session_id || Date.now(),
        persona_id: simulationData?.persona?.id,
        situation_id: simulationData?.situation?.id,
        user_id: user?.id,
        timestamp: new Date().toISOString()
      }))

      // FormData는 브라우저가 자동으로 Content-Type을 설정하므로 헤더 제거
      const response = await api.post('/rag-simulation/upload-recording', formData, {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            console.log(`업로드 진행률: ${percentCompleted}%`)
          }
        }
      })

      console.log('✅ 녹화 파일 업로드 완료:', response.data)
      
      // 사용자에게 알림 (선택사항)
      if (response.data?.video_url) {
        console.log('📹 녹화 파일 URL:', response.data.video_url)
        // 필요시 상태 업데이트 또는 토스트 메시지 표시
      }
    } catch (error) {
      console.error('❌ 녹화 파일 업로드 실패:', error)
      // 업로드 실패해도 시뮬레이션은 계속 진행
    }
  }

  // 음성 녹음 시작 (화면 녹화 포함)
  const startRecording = async () => {
    try {
      // 오디오 스트림 가져오기
      const audioStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      })
      
      // 스트림을 state에 저장 (시각화용)
      setStream(audioStream)
      
      // 오디오 녹음용 MediaRecorder (STT용)
      mediaRecorderRef.current = new MediaRecorder(audioStream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mediaRecorderRef.current?.mimeType || 'audio/webm'
        })
        console.log('녹음된 오디오 Blob:', audioBlob)
        console.log('Blob 크기:', audioBlob.size)
        
        // 오디오 스트림 정리
        audioStream.getTracks().forEach(track => track.stop())
        setStream(null)
        
        processAudio(audioBlob)
      }

      mediaRecorderRef.current.start()
      
      // 화면 녹화 시작 (비디오 + 오디오 함께)
      if (videoStream && audioStream) {
        console.log('🎬 화면 녹화 시작...')
        
        // 비디오 트랙과 오디오 트랙 합치기
        const combinedStream = new MediaStream()
        videoStream.getVideoTracks().forEach(track => {
          combinedStream.addTrack(track)
          console.log('✅ 비디오 트랙 추가:', track.label)
        })
        audioStream.getAudioTracks().forEach(track => {
          combinedStream.addTrack(track)
          console.log('✅ 오디오 트랙 추가:', track.label)
        })

        // 화면 녹화용 MediaRecorder
        const videoMimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus') 
          ? 'video/webm;codecs=vp9,opus'
          : MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus')
          ? 'video/webm;codecs=vp8,opus'
          : 'video/webm'
        
        videoRecorderRef.current = new MediaRecorder(combinedStream, {
          mimeType: videoMimeType,
          videoBitsPerSecond: 2500000 // 2.5 Mbps
        })
        videoChunksRef.current = []

        videoRecorderRef.current.ondataavailable = (event) => {
          if (event.data.size > 0) {
            videoChunksRef.current.push(event.data)
            console.log('📹 화면 녹화 데이터 수신:', event.data.size, 'bytes')
          }
        }

        videoRecorderRef.current.onstop = async () => {
          const videoBlob = new Blob(videoChunksRef.current, { 
            type: videoRecorderRef.current?.mimeType || 'video/webm'
          })
          console.log('✅ 화면 녹화 완료:', videoBlob.size, 'bytes')
          
          // 백엔드로 업로드
          await uploadRecording(videoBlob)
        }

        videoRecorderRef.current.start(1000) // 1초마다 데이터 수집
        console.log('✅ 화면 녹화 시작됨')
      }

      setIsRecording(true)
      setSubtitle('말씀해주세요...')
    } catch (error) {
      console.error('녹음 시작 실패:', error)
      setError('마이크 접근 권한이 필요합니다.')
    }
  }

  // 음성 녹음 중지 (화면 녹화도 함께 중지)
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setSubtitle('음성을 처리 중입니다...')
    }
    
    // 화면 녹화도 중지
    if (videoRecorderRef.current && videoRecorderRef.current.state !== 'inactive') {
      console.log('🛑 화면 녹화 중지 중...')
      videoRecorderRef.current.stop()
    }
  }

  // 음성 처리 및 STT - 상세 로그 + 방탄 분기
  const processAudio = async (audioBlob: Blob) => {
    console.groupCollapsed('🚀 음성 인터랙션 요청');
    console.log('보내는 파일:', audioBlob?.type, audioBlob?.size, 'bytes');
    
    try {
      setLoading(true)
      setError('')

      // 세션 데이터에 대화 히스토리 포함
      const sessionDataWithHistory = {
        ...simulationData,
        conversation_history: chatHistory.map(msg => ({
          role: msg.role === 'user' ? 'employee' : 'customer',
          text: msg.text,
          timestamp: msg.timestamp.toISOString()
        })),
        achieved_goals: Array.from(checkedGoals) // 달성된 목표 포함
      }

      const formData = new FormData()
      formData.append('audio_file', audioBlob, 'recording.webm')  // 서버가 audio_file을 기대
      formData.append('session_data', JSON.stringify(sessionDataWithHistory))

      console.log('FormData 준비 완료, 전송 시작...');

      const response = await api.post('/rag-simulation/process-voice-interaction', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      console.log('✅ 응답 원본:', response.data);
      const { transcribed_text, customer_response, customer_audio } = response.data
      
      // 대화 종료 표현 확인
      let isEndMessage = false
      if (transcribed_text) {
        isEndMessage = checkConversationEnd(transcribed_text)
        if (isEndMessage) {
          console.log('🔚 종료 표현 감지:', transcribed_text)
        }
      }
      
      // 오디오 페이로드 디버깅
      console.log('오디오 페이로드 타입:', typeof customer_audio);
      console.log('오디오 페이로드 미리보기:', typeof customer_audio === 'string' ? customer_audio.substring(0, 100) : customer_audio);

      console.log('API 응답 데이터:', { transcribed_text, customer_response, customer_audio: customer_audio ? customer_audio.substring(0, 100) + '...' : null })

      // 대화 히스토리에 사용자 메시지 추가
      if (transcribed_text) {
        setChatHistory((prev: ChatMessage[]) => [...prev, {
          id: Date.now().toString(),
          role: 'user',
          text: transcribed_text,
          timestamp: new Date()
        }])
      }

      // 대화 히스토리에 고객 메시지 추가
      if (customer_response) {
        setChatHistory((prev: ChatMessage[]) => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'customer',
          text: customer_response,
          audio: customer_audio,
          timestamp: new Date()
        }])

        // 🔥 아바타가 말하도록 설정
        if (customer_audio) {
          setAudio({
            audioUrl: customer_audio,
            text: customer_response,
            mouthCues: [] // TODO: Rhubarb로 생성
          })
        }
      }

      // 사용자 입력 필드 초기화
      setUserMessage('')

      // 고객 음성 재생 - 새로운 유틸 사용
      if (customer_audio) {
        try {
          console.log('🎵 오디오 재생 시도...');
          await playFromAnyAudioPayload(customer_audio, 'audio/mpeg');
          setIsPlaying(true);
          setError('');
          
          // 종료 플래그가 설정되어 있으면 오디오 재생 후 시뮬레이션 종료
          if (isEndMessage) {
            const responseLength = customer_response?.length || 0
            const estimatedAudioDuration = Math.max(3000, Math.min(responseLength * 100, 8000))
            setTimeout(() => {
              console.log('🔚 대화 종료: 고객 응답 재생 완료 후 종료')
              handleEndSimulation()
            }, estimatedAudioDuration)
          }
        } catch (audioError) {
          console.error('오디오 재생 실패:', audioError);
          setError('오디오 재생에 실패했습니다.');
          
          // 오디오 재생 실패 시에도 종료 플래그가 설정되어 있으면 종료
          if (isEndMessage) {
            setTimeout(() => {
              console.log('🔚 대화 종료: 오디오 재생 실패로 인한 종료')
              handleEndSimulation()
            }, 2000)
          }
        }
      } else {
        console.log('오디오 데이터가 없습니다. 텍스트만 표시됩니다.')
        
        // 오디오가 없을 때도 종료 플래그가 설정되어 있으면 종료
        if (isEndMessage) {
          setTimeout(() => {
            console.log('🔚 대화 종료: 오디오 없음으로 인한 종료')
            handleEndSimulation()
          }, 3000)
        }
      }

      setSubtitle('')

    } catch (error: any) {
      console.error('❌ 음성 처리 실패:', error)
      setError('음성 처리를 실패했습니다. 다시 시도해주세요.')
    } finally {
      setLoading(false)
      console.groupEnd();
    }
  }

  // 텍스트 입력으로도 시뮬레이션 가능
  const handleTextSubmit = async () => {
    if (!userMessage.trim()) return

    // 대화 종료 표현 확인
    const isEndMessage = checkConversationEnd(userMessage)
    if (isEndMessage) {
      console.log('🔚 종료 표현 감지:', userMessage)
    }

    console.groupCollapsed('💬 텍스트 인터랙션 요청');

    try {
      setLoading(true)
      setError('')

      console.log('전송할 메시지:', userMessage);
      console.log('세션 데이터:', simulationData);
      console.log('세션 데이터 키:', Object.keys(simulationData || {}));

      // 세션 데이터에 대화 히스토리 및 달성된 목표 포함
      const sessionDataWithHistory = {
        ...simulationData,
        conversation_history: chatHistory.map(msg => ({
          role: msg.role === 'user' ? 'employee' : 'customer',
          text: msg.text,
          timestamp: msg.timestamp.toISOString()
        })),
        achieved_goals: Array.from(checkedGoals) // 달성된 목표 포함
      }

      // JSON으로 전송
      const requestData = {
        session_data: sessionDataWithHistory,
        user_message: userMessage
      };

      console.log('요청 데이터 구조:', {
        session_data_keys: Object.keys(requestData.session_data || {}),
        user_message: requestData.user_message
      });

      // JSON으로 직접 전송 (Axios가 자동으로 Content-Type 설정)
      const response = await api.post('/rag-simulation/process-voice-interaction', requestData)

      console.log('✅ 응답 원본:', response.data);
      
      if (!response.data) {
        console.error('응답 데이터가 없습니다');
        setError('서버 응답이 비어있습니다.');
        return;
      }

      const { customer_response, customer_audio } = response.data

      console.log('고객 응답:', customer_response);
      console.log('고객 오디오 있음:', !!customer_audio);

      // 대화 히스토리에 사용자 메시지 추가
      setChatHistory((prev: ChatMessage[]) => [...prev, {
        id: Date.now().toString(),
        role: 'user',
        text: userMessage,
        timestamp: new Date()
      }])

      // 대화 히스토리에 고객 메시지 추가
      if (customer_response) {
        setChatHistory((prev: ChatMessage[]) => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'customer',
          text: customer_response,
          audio: customer_audio,
          timestamp: new Date()
        }])

        // 🔥 아바타가 말하도록 설정
        if (customer_audio) {
          setAudio({
            audioUrl: customer_audio,
            text: customer_response,
            mouthCues: [] // TODO: Rhubarb로 생성
          })
        }
      }

      // 사용자 입력 필드 초기화
      setUserMessage('')

      // 오디오 재생 - 새로운 유틸 사용
      if (customer_audio) {
        try {
          console.log('🎵 오디오 재생 시도...');
          await playFromAnyAudioPayload(customer_audio, 'audio/mpeg');
          setIsPlaying(true);
          setError('');
          
          // 종료 플래그가 설정되어 있으면 오디오 재생 후 시뮬레이션 종료 (고객 응답을 듣는 시간 제공)
          if (isEndMessage) {
            // 고객 응답 길이를 고려하여 대기 시간 설정 (평균적으로 3-5초 정도)
            const responseLength = customer_response?.length || 0
            const estimatedAudioDuration = Math.max(3000, Math.min(responseLength * 100, 8000)) // 최소 3초, 최대 8초
            setTimeout(() => {
              console.log('🔚 대화 종료: 고객 응답 재생 완료 후 종료')
              handleEndSimulation()
            }, estimatedAudioDuration)
          }
        } catch (audioError) {
          console.error('오디오 재생 실패:', audioError);
          setError('오디오 재생에 실패했습니다.');
          
          // 오디오 재생 실패 시에도 종료 플래그가 설정되어 있으면 종료
          if (isEndMessage) {
            setTimeout(() => {
              console.log('🔚 대화 종료: 오디오 재생 실패로 인한 종료')
              handleEndSimulation()
            }, 2000)
          }
        }
      } else {
        console.log('오디오 데이터가 없습니다. 텍스트만 표시됩니다.');
        
        // 오디오가 없을 때도 종료 플래그가 설정되어 있으면 종료
        if (isEndMessage) {
          setTimeout(() => {
            console.log('🔚 대화 종료: 오디오 없음으로 인한 종료')
            handleEndSimulation()
          }, 3000) // 고객 응답 텍스트를 읽을 시간 제공
        }
      }

    } catch (error: any) {
      console.error('❌ 텍스트 처리 실패:', error)
      console.error('에러 상세:', error?.response?.data || error?.message)
      setError(`메시지 처리를 실패했습니다: ${error?.response?.data?.detail || error?.message || '알 수 없는 오류'}`)
    } finally {
      setLoading(false)
      console.groupEnd();
    }
  }

  // 오디오 재생 완료 처리 및 자동 재생 준비
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.onended = () => {
        setIsPlaying(false)
        // URL 객체 정리
        if (audioRef.current?.src && audioRef.current.src.startsWith('blob:')) {
          URL.revokeObjectURL(audioRef.current.src)
        }
      }
      
      audioRef.current.onerror = () => {
        setIsPlaying(false)
        setError('오디오 재생 중 오류가 발생했습니다.')
      }
    }
  }, [])

  // 시뮬레이션 완료 페이지
  if (isSimulationCompleted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-6 relative">
        {/* 배경 블러 오버레이 */}
        <div className="absolute inset-0 bg-black bg-opacity-10 backdrop-blur-sm"></div>
        
        {/* 완료 카드 */}
        <div className="relative bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full animate-fade-in z-10">
          <style>{`
            @keyframes fade-in {
              from {
                opacity: 0;
                transform: translateY(-20px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
            .animate-fade-in {
              animation: fade-in 0.3s ease-out;
            }
          `}</style>
          
          {/* 체크 아이콘 */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
              <CheckIcon className="w-12 h-12 text-green-600" />
            </div>
          </div>
          
          {/* 완료 메시지 */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              시뮬레이션이 완료되었습니다
            </h2>
            <p className="text-gray-600 text-lg">
              고객과의 대화가 종료되었습니다.
            </p>
            <p className="text-gray-600 text-lg mt-2">
              이제 신입사원 응대에 대한 평가를 진행해 주세요.
            </p>
          </div>
          
          {/* 통계 (선택사항) */}
          <div className="mb-8 grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-blue-600">{chatHistory.length}</div>
              <div className="text-sm text-gray-600 mt-1">대화 턴</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600">{checkedGoals.size}</div>
              <div className="text-sm text-gray-600 mt-1">달성 목표</div>
            </div>
          </div>
          
          {/* 버튼 그룹 */}
          <div className="space-y-4">
            <button
              onClick={handleGoToEvaluation}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-4 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
            >
              📝 평가 페이지로 이동
            </button>
            
            <button
              onClick={handleRestartSimulation}
              className="w-full bg-gray-100 text-gray-700 font-semibold py-4 px-6 rounded-lg hover:bg-gray-200 transition-all duration-200 border border-gray-300"
            >
              🔁 다시 시뮬레이션하기
            </button>
            
            <button
              onClick={onBack}
              className="w-full text-gray-500 hover:text-gray-700 font-medium py-2 px-4 transition-colors"
            >
              뒤로가기
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* 왼쪽: 시뮬레이션 정보 패널 */}
      <div className="w-80 bg-white border-r border-gray-200 p-6 overflow-y-auto">
        <div className="mb-6">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            뒤로가기
          </button>
          <h2 className="text-xl font-bold text-gray-900">시뮬레이션 정보</h2>
        </div>

        {/* 고객 정보 */}
        <div className="mb-6">
          <button
            onClick={() => setIsCustomerInfoOpen(!isCustomerInfoOpen)}
            className="w-full flex items-center justify-between font-semibold text-gray-700 mb-3 hover:text-gray-900 transition-colors"
          >
            <span>고객 정보</span>
            {isCustomerInfoOpen ? (
              <ChevronUpIcon className="w-5 h-5" />
            ) : (
              <ChevronDownIcon className="w-5 h-5" />
            )}
          </button>
          {isCustomerInfoOpen && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">성별:</span>
                <span className="font-medium text-gray-900">
                  {simulationData?.persona?.gender || '미설정'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">연령대:</span>
                <span className="font-medium text-gray-900">
                  {simulationData?.persona?.age_group || '미설정'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">직업:</span>
                <span className="font-medium text-gray-900">
                  {simulationData?.persona?.occupation || '미설정'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">고객 타입:</span>
                <span className="font-medium text-gray-900">
                  {simulationData?.persona?.type || '미설정'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* 상황 정보 */}
        <div>
          <button
            onClick={() => setIsSituationInfoOpen(!isSituationInfoOpen)}
            className="w-full flex items-center justify-between font-semibold text-gray-700 mb-3 hover:text-gray-900 transition-colors"
          >
            <span>상황 정보</span>
            {isSituationInfoOpen ? (
              <ChevronUpIcon className="w-5 h-5" />
            ) : (
              <ChevronDownIcon className="w-5 h-5" />
            )}
          </button>
          {isSituationInfoOpen && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">업무 카테고리:</span>
                <span className="font-medium text-gray-900">
                  {simulationData?.situation?.category || '미설정'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">상황 제목:</span>
                <div className="font-medium text-gray-900 mt-1">
                  {simulationData?.situation?.title || '미설정'}
                </div>
              </div>
              {simulationData?.situation?.goals && simulationData.situation.goals.length > 0 && (
                <div className="mt-3">
                  <span className="text-gray-600 text-sm block mb-1">목표:</span>
                  <ul className="space-y-2">
                    {simulationData.situation.goals.map((goal: string, index: number) => {
                      const isChecked = checkedGoals.has(index)
                      return (
                        <li
                          key={index}
                          className={`flex items-start gap-2 text-sm text-gray-700 rounded p-2 -ml-2 transition-colors ${
                            isChecked ? 'bg-green-50' : ''
                          }`}
                        >
                          <div className={`flex-shrink-0 mt-0.5 ${
                            isChecked ? 'text-green-600' : 'text-gray-400'
                          }`}>
                            {isChecked ? (
                              <CheckIcon className="w-5 h-5" />
                            ) : (
                              <div className="w-5 h-5 border-2 border-gray-300 rounded" />
                            )}
                          </div>
                          <span className={isChecked ? 'text-green-700 line-through' : ''}>
                            {goal}
                          </span>
                        </li>
                      )
                    })}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 오른쪽: 메인 시뮬레이션 영역 */}
      <div className="flex-1 flex flex-col bg-white">
        {/* 시작 전 화면 */}
        {!isStarted && (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">시뮬레이션 준비</h1>
              <p className="text-gray-600 mb-8">시뮬레이션을 시작하려면 아래 버튼을 눌러주세요.</p>
              <button
                onClick={() => {
                  setIsStarted(true)
                  setIsInitializing(true)
                }}
                className="px-12 py-4 bg-blue-600 text-white text-xl font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
              >
                시뮬레이션 시작하기
              </button>
            </div>
          </div>
        )}

        {/* 시작 후 화면 */}
        {isStarted && (
          <>
            {/* 비디오 영역 */}
            <div className="flex-1 flex items-center justify-center bg-gray-900 relative min-h-0">
              {/* 사용자 카메라 */}
              <div className="absolute inset-0 w-full h-full flex items-center justify-center">
                {videoStream ? (
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                    style={{ transform: 'scaleX(-1)' }}
                  />
                ) : (
                  <div className="text-white text-center z-10">
                    <VideoCameraIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-400">카메라를 불러오는 중...</p>
                    {error && (
                      <p className="text-red-400 mt-2 text-sm">{error}</p>
                    )}
                  </div>
                )}
                
                {/* 고객 아바타 오버레이 (우측 하단) */}
                <div className="absolute bottom-4 right-4 w-48 h-48">
                  <CustomerAvatar className="w-full h-full" />
                </div>
              </div>

              {/* 녹음 버튼 (하단 중앙) */}
              <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
                {!isRecording ? (
                  <button
                    onClick={startRecording}
                    disabled={loading || isInitializing}
                    className="flex items-center px-8 py-4 bg-red-600 text-white rounded-full hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors shadow-2xl"
                  >
                    <MicrophoneIcon className="w-6 h-6 mr-2" />
                    {isInitializing ? '준비 중...' : '녹음 시작'}
                  </button>
                ) : (
                  <button
                    onClick={stopRecording}
                    className="flex items-center px-8 py-4 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors shadow-2xl animate-pulse"
                  >
                    <StopIcon className="w-6 h-6 mr-2" />
                    녹음 중지
                  </button>
                )}
              </div>

              {/* 실시간 자막 */}
              {subtitle && (
                <div className="absolute top-8 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-75 text-white px-6 py-3 rounded-lg">
                  {subtitle}
                </div>
              )}
            </div>

            {/* 채팅 히스토리 */}
            <div className="h-48 bg-white border-t border-gray-200 p-4 overflow-y-auto">
              <h3 className="font-semibold text-gray-900 mb-4">대화</h3>
              
              <div className="space-y-3" style={{ scrollBehavior: 'smooth' }}>
                {isInitializing ? (
                  <div className="text-center text-gray-500 py-8">
                    <div className="flex items-center justify-center">
                      <ArrowPathIcon className="w-5 h-5 mr-2 animate-spin" />
                      고객의 첫 인사를 준비하고 있습니다...
                    </div>
                  </div>
                ) : chatHistory.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    대화를 시작하세요. 녹음 버튼을 눌러거나 텍스트를 입력하세요.
                  </div>
                ) : (
                  chatHistory.map((message) => (
                    <div
                      key={message.id}
                      className={`p-4 rounded-lg ${
                        message.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-green-50 mr-8'
                      }`}
                    >
                      <div className="flex items-center mb-2">
                        <span className={`font-medium ${
                          message.role === 'user' ? 'text-blue-800' : 'text-green-800'
                        }`}>
                          {message.role === 'user' ? '신입사원 (나)' : '고객'}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <p className={message.role === 'user' ? 'text-blue-700' : 'text-green-700'}>
                        {message.text}
                      </p>
                      {message.role === 'customer' && message.audio && (
                        <button
                          onClick={() => {
                            if (message.audio) {
                              playFromAnyAudioPayload(message.audio, 'audio/mpeg')
                            }
                          }}
                          className="mt-2 flex items-center px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                        >
                          <SpeakerWaveIcon className="w-3 h-3 mr-1" />
                          다시 듣기
                        </button>
                      )}
                    </div>
                  ))
                )}
                <div ref={chatEndRef} />
              </div>

              {/* 텍스트 입력 (하단) */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleTextSubmit()}
                    placeholder={isInitializing ? "고객의 첫 인사를 기다리는 중..." : "메시지를 입력하세요..."}
                    disabled={isInitializing}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <button
                    onClick={handleTextSubmit}
                    disabled={loading || !userMessage.trim() || isInitializing}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    전송
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* 오류 메시지 */}
        {error && (
          <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* 오디오 엘리먼트 */}
        <audio ref={audioRef} />
      </div>
    </div>
  )
}

export default VoiceSimulation
