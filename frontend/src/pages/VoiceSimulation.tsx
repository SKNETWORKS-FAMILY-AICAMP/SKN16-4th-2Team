import React, { useState, useRef, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { usePersonaStore } from '../store/usePersonaStore'
import api from '../utils/api'
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
  VideoCameraIcon
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
        }))
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
        } catch (audioError) {
          console.error('오디오 재생 실패:', audioError);
          setError('오디오 재생에 실패했습니다.');
        }
      } else {
        console.log('오디오 데이터가 없습니다. 텍스트만 표시됩니다.')
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

    console.groupCollapsed('💬 텍스트 인터랙션 요청');

    try {
      setLoading(true)
      setError('')

      console.log('전송할 메시지:', userMessage);
      console.log('세션 데이터:', simulationData);
      console.log('세션 데이터 키:', Object.keys(simulationData || {}));

      // 세션 데이터에 대화 히스토리 포함
      const sessionDataWithHistory = {
        ...simulationData,
        conversation_history: chatHistory.map(msg => ({
          role: msg.role === 'user' ? 'employee' : 'customer',
          text: msg.text,
          timestamp: msg.timestamp.toISOString()
        }))
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
        } catch (audioError) {
          console.error('오디오 재생 실패:', audioError);
          setError('오디오 재생에 실패했습니다.');
        }
      } else {
        console.log('오디오 데이터가 없습니다. 텍스트만 표시됩니다.');
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
          <h3 className="font-semibold text-gray-700 mb-3">고객 정보</h3>
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
        </div>

        {/* 상황 정보 */}
        <div>
          <h3 className="font-semibold text-gray-700 mb-3">상황 정보</h3>
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
                <ul className="space-y-1">
                  {simulationData.situation.goals.map((goal: string, index: number) => (
                    <li key={index} className="text-sm text-gray-700">• {goal}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
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
                    대화를 시작하세요. 녹음 버튼을 누르거나 텍스트를 입력하세요.
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
