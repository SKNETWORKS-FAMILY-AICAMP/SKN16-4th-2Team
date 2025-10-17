/**
 * 대시보드 페이지
 * 멘티/멘토별 맞춤 대시보드
 */
import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { dashboardAPI } from '../utils/api'
import { 
  UserIcon,
  AcademicCapIcon,
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  TrashIcon,
  ChatBubbleBottomCenterTextIcon,
  TrophyIcon,
  EyeIcon,
  PencilIcon,
  ChartBarIcon,
  LightBulbIcon,
  StarIcon
} from '@heroicons/react/24/outline'
import { 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  ResponsiveContainer,
  Tooltip
} from 'recharts'
import { motion } from 'framer-motion'

export default function Dashboard() {
  const { user } = useAuthStore()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    loadDashboard()
  }, [user])

  // 실시간 시간 업데이트 (30초마다)
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date())
    }, 30000) // 30초마다 업데이트

    return () => clearInterval(interval)
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      // 현재 시간을 정확하게 설정
      setCurrentTime(new Date())
      
      if (user?.role === 'mentee') {
        const dashboardData = await dashboardAPI.getMenteeDashboard()
        setData(dashboardData)
      } else if (user?.role === 'mentor' || user?.role === 'admin') {
        const dashboardData = await dashboardAPI.getMentorDashboard()
        setData(dashboardData)
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (user?.role === 'mentee') {
    return <MenteeDashboard data={data} currentTime={currentTime} />
  } else if (user?.role === 'mentor' || user?.role === 'admin') {
    return <MentorDashboard data={data} />
  }

  return null
}

function MenteeDashboard({ data, currentTime }: any) {
  // 6가지 지표 성적표 데이터
  const performanceData = [
    { skill: '은행업무', score: data?.performance_scores?.banking || 85 },
    { skill: '상품지식', score: data?.performance_scores?.product_knowledge || 78 },
    { skill: '고객응대', score: data?.performance_scores?.customer_service || 92 },
    { skill: '법규준수', score: data?.performance_scores?.compliance || 88 },
    { skill: 'IT활용', score: data?.performance_scores?.it_usage || 75 },
    { skill: '영업실적', score: data?.performance_scores?.sales_performance || 80 }
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">내 대시보드</h1>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-6">
        <StatCard
          icon={ChatBubbleBottomCenterTextIcon}
          title="총 대화 수"
          value={data?.learning_progress?.total_chats || 0}
          color="primary"
        />
        <StatCard
          icon={AcademicCapIcon}
          title="학습 진행도"
          value={`${data?.learning_progress?.progress_percentage || 0}%`}
          color="amber"
        />
        <StatCard
          icon={TrophyIcon}
          title="최근 시험 점수"
          value={data?.exam_scores?.[0]?.total_score?.toFixed(1) || 'N/A'}
          color="bank"
        />
      </div>

      {/* Performance Radar Chart - 6가지 지표 성적표 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center mb-6">
          <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
          <h2 className="text-2xl font-bold text-bank-800">성과 지표 분석</h2>
        </div>
        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-1">
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={performanceData}>
                <PolarGrid 
                  stroke="#e5e7eb" 
                  strokeWidth={1}
                />
                <PolarAngleAxis 
                  dataKey="skill" 
                  tick={{ fontSize: 12, fill: '#374151' }}
                  axisLine={{ stroke: '#9ca3af' }}
                />
                <PolarRadiusAxis 
                  angle={90} 
                  domain={[0, 100]} 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                  axisLine={false}
                  tickLine={{ stroke: '#d1d5db' }}
                />
                <Radar
                  name="점수"
                  dataKey="score"
                  stroke="#d4a574"
                  fill="#d4a574"
                  fillOpacity={0.3}
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#d4a574' }}
                />
                <Tooltip 
                  formatter={(value: any) => [`${value}점`, '점수']}
                  labelFormatter={(label: string) => `지표: ${label}`}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="w-full lg:w-80">
            <div className="space-y-3">
              {performanceData.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">{item.skill}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${item.score}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-bold text-gray-900 w-10 text-right">
                      {item.score}점
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 p-4 bg-gradient-to-r from-primary-50 to-amber-50 rounded-xl border border-primary-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-primary-900">종합 점수</span>
                <span className="text-lg font-bold text-primary-600">
                  {(performanceData.reduce((sum, item) => sum + item.score, 0) / performanceData.length).toFixed(1)}점
                </span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Mentor Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center mb-6">
          <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
          <h2 className="text-2xl font-bold text-bank-800">담당 멘토</h2>
        </div>
        {data?.mentor_info ? (
          <div className="flex items-start space-x-4">
            {data.mentor_info.photo_url ? (
              <img
                src={data.mentor_info.photo_url}
                alt={data.mentor_info.name}
                className="w-16 h-16 rounded-full"
              />
            ) : (
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
                <UserIcon className="w-8 h-8 text-primary-600" />
              </div>
            )}
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900">{data.mentor_info.name}</h3>
              <p className="text-gray-600 text-sm">
                {data.mentor_info.team} • MBTI: {data.mentor_info.mbti}
              </p>
              {data.mentor_info.interests && (
                <p className="text-gray-600 text-sm mt-1">관심사: {data.mentor_info.interests}</p>
              )}
              {data.mentor_info.encouragement_message && (
                <div className="mt-3 p-4 bg-gradient-to-r from-primary-50 to-amber-50 rounded-xl border border-primary-200">
                  <p className="text-primary-800 text-sm italic">
                    "{data.mentor_info.encouragement_message}"
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <UserIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg mb-2">아직 담당 멘토가 배정되지 않았습니다</p>
            <p className="text-gray-400 text-sm">관리자에게 멘토 배정을 요청해보세요</p>
          </div>
        )}
      </motion.div>

      {/* Recent Feedbacks */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
            <h2 className="text-2xl font-bold text-bank-800">멘토 피드백</h2>
          </div>
          {data?.recent_feedbacks && data.recent_feedbacks.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">총 {data.recent_feedbacks.length}개</span>
              {(() => {
                const recentCount = data.recent_feedbacks.filter((f: any) => {
                  const feedbackDate = new Date(f.created_at)
                  const diffInHours = (currentTime.getTime() - feedbackDate.getTime()) / (1000 * 60 * 60)
                  return diffInHours <= 24 && !f.is_read
                }).length
                
                if (recentCount > 0) {
                  return (
                    <span className="px-2 py-1 bg-accent-100 text-accent-800 text-xs rounded-full animate-pulse">
                      최신 피드백 {recentCount}개
                    </span>
                  )
                } else if (data.recent_feedbacks.filter((f: any) => !f.is_read).length > 0) {
                  return (
                    <span className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full">
                      새 피드백 {data.recent_feedbacks.filter((f: any) => !f.is_read).length}개
                    </span>
                  )
                }
                return null
              })()}
            </div>
          )}
        </div>
        
        {data?.recent_feedbacks && data.recent_feedbacks.length > 0 ? (
          <div className="space-y-3">
            {data.recent_feedbacks.slice(0, 3).map((feedback: any, idx: number) => (
              <FeedbackCard key={idx} feedback={feedback} index={idx} currentTime={currentTime} />
            ))}
            
            {/* 더 많은 피드백이 있을 때 */}
            {data.recent_feedbacks.length > 3 && (
              <FeedbackAccordion 
                additionalFeedbacks={data.recent_feedbacks.slice(3)} 
                totalCount={data.recent_feedbacks.length}
                currentTime={currentTime}
              />
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <ChatBubbleLeftRightIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg mb-2">아직 받은 피드백이 없습니다</p>
            <p className="text-gray-400 text-sm">멘토가 피드백을 보내면 여기에 표시됩니다</p>
          </div>
        )}
      </motion.div>

      {/* Recent Chats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center mb-6">
          <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
          <h2 className="text-2xl font-bold text-bank-800">최근 대화</h2>
        </div>
        {data?.recent_chats && data.recent_chats.length > 0 ? (
          <div className="space-y-4">
            {data.recent_chats.slice(0, 5).map((chat: any, idx: number) => (
              <div key={idx} className="p-4 bg-gradient-to-r from-primary-50 to-amber-50 rounded-xl border border-primary-100">
                <p className="font-medium text-bank-800 mb-1">{chat.user_message}</p>
                <p className="text-sm text-primary-700 line-clamp-2">{chat.bot_response}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <ChatBubbleBottomCenterTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 text-lg mb-2">아직 대화 기록이 없습니다</p>
            <p className="text-gray-400 text-sm">챗봇과 대화를 시작해보세요</p>
          </div>
        )}
      </motion.div>
    </div>
  )
}

function MentorDashboard({ data }: any) {
  const [selectedMentee, setSelectedMentee] = useState<any>(null)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [showPerformanceModal, setShowPerformanceModal] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')

  const handleGiveFeedback = (mentee: any) => {
    setSelectedMentee(mentee)
    setShowFeedbackModal(true)
  }

  const handleViewPerformance = (mentee: any) => {
    setSelectedMentee(mentee)
    setShowPerformanceModal(true)
  }

  const submitFeedback = async () => {
    try {
      await dashboardAPI.createFeedback(selectedMentee.id, feedbackText, 'general')
      alert('피드백이 성공적으로 전송되었습니다!')
      setShowFeedbackModal(false)
      setFeedbackText('')
      setSelectedMentee(null)
      // 페이지 새로고침하여 최신 데이터 반영
      window.location.reload()
    } catch (error) {
      console.error('피드백 전송 실패:', error)
      alert('피드백 전송에 실패했습니다. 다시 시도해주세요.')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">멘토 대시보드</h1>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-6">
        <StatCard
          icon={UserIcon}
          title="담당 멘티"
          value={data?.mentees?.length || 0}
          color="primary"
        />
        <StatCard
          icon={ChatBubbleBottomCenterTextIcon}
          title="자주 묻는 질문"
          value={data?.frequent_questions?.length || 0}
          color="amber"
        />
        <StatCard
          icon={AcademicCapIcon}
          title="평균 성적"
          value={
            data?.mentees?.length > 0
              ? (
                  data.mentees.reduce((sum: number, m: any) => sum + (m.recent_score || 0), 0) /
                  data.mentees.length
                ).toFixed(1)
              : 'N/A'
          }
          color="bank"
        />
        <StatCard
          icon={ChartBarIcon}
          title="활성 멘티"
          value={data?.mentees?.filter((m: any) => m.chat_count > 0)?.length || 0}
          color="accent"
        />
      </div>

      {/* Mentees List with Enhanced Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center mb-6">
          <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
          <h2 className="text-2xl font-bold text-bank-800">담당 멘티 관리</h2>
        </div>
        <div className="grid gap-6">
          {data?.mentees?.map((mentee: any) => (
            <MenteeCard 
              key={mentee.id} 
              mentee={mentee} 
              onGiveFeedback={handleGiveFeedback}
              onViewPerformance={handleViewPerformance}
            />
          ))}
          {(!data?.mentees || data.mentees.length === 0) && (
            <div className="text-center py-12">
              <UserIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">담당 멘티가 없습니다</p>
              <p className="text-gray-400 text-sm mt-2">관리자에게 멘티 배정을 요청해보세요</p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Feedback Modal */}
      {showFeedbackModal && selectedMentee && (
        <FeedbackModal
          mentee={selectedMentee}
          feedbackText={feedbackText}
          setFeedbackText={setFeedbackText}
          onSubmit={submitFeedback}
          onClose={() => setShowFeedbackModal(false)}
        />
      )}

      {/* Performance Modal */}
      {showPerformanceModal && selectedMentee && (
        <PerformanceModal
          mentee={selectedMentee}
          onClose={() => setShowPerformanceModal(false)}
        />
      )}

      {/* Frequent Questions */}
      {data?.frequent_questions && data.frequent_questions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
        >
          <div className="flex items-center mb-6">
            <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
            <h2 className="text-2xl font-bold text-bank-800">담당 멘티 자주 묻는 질문</h2>
          </div>
          <div className="flex flex-wrap gap-3">
            {data.frequent_questions.slice(0, 20).map((item: any, idx: number) => (
              <span
                key={idx}
                className="px-4 py-2 bg-gradient-to-r from-primary-100 to-amber-100 text-primary-800 rounded-xl text-sm font-medium border border-primary-200 hover:shadow-md transition-all duration-200"
                style={{ fontSize: `${Math.min(16, 12 + item.count / 2)}px` }}
              >
                {item.word} ({item.count})
              </span>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

// 멘티 카드 컴포넌트
function MenteeCard({ mentee, onGiveFeedback, onViewPerformance }: any) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-blue-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getPerformanceLevel = (score: number) => {
    if (score >= 90) return '우수'
    if (score >= 80) return '양호'
    if (score >= 70) return '보통'
    return '개선 필요'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-white to-gray-50 rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-all duration-300"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-4">
          {mentee.photo_url ? (
            <img src={mentee.photo_url} alt={mentee.name} className="w-16 h-16 rounded-full" />
          ) : (
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
              <UserIcon className="w-8 h-8 text-primary-600" />
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 mb-1">{mentee.name}</h3>
            <p className="text-gray-600 mb-2">
              {mentee.team} • MBTI: {mentee.mbti || '미설정'}
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <ChatBubbleBottomCenterTextIcon className="w-4 h-4 mr-1" />
                대화 {mentee.chat_count || 0}회
              </span>
              <span className="flex items-center">
                <StarIcon className="w-4 h-4 mr-1" />
                {getPerformanceLevel(mentee.recent_score || 0)}
              </span>
            </div>
          </div>
        </div>
        
        <div className="text-right">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm text-gray-600">최근 점수</span>
            <span className={`text-2xl font-bold ${getScoreColor(mentee.recent_score || 0)}`}>
              {mentee.recent_score?.toFixed(1) || 'N/A'}
            </span>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => onViewPerformance(mentee)}
              className="flex items-center px-3 py-2 bg-primary-100 text-primary-700 rounded-lg hover:bg-primary-200 transition-colors text-sm"
            >
              <EyeIcon className="w-4 h-4 mr-1" />
              성과 분석
            </button>
            <button
              onClick={() => onGiveFeedback(mentee)}
              className="flex items-center px-3 py-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors text-sm"
            >
              <PencilIcon className="w-4 h-4 mr-1" />
              피드백
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

// 피드백 모달 컴포넌트
function FeedbackModal({ mentee, feedbackText, setFeedbackText, onSubmit, onClose }: any) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl p-6 w-full max-w-md mx-4"
      >
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          {mentee.name}님에게 피드백 주기
        </h3>
        <textarea
          value={feedbackText}
          onChange={(e) => setFeedbackText(e.target.value)}
          placeholder="멘티에게 전달할 피드백을 작성해주세요..."
          className="w-full h-32 p-3 border border-primary-200 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <div className="flex space-x-3 mt-4">
          <button
            onClick={onSubmit}
            disabled={!feedbackText.trim()}
            className="flex-1 bg-gradient-to-r from-primary-600 to-primary-500 text-white py-2 px-4 rounded-lg hover:from-primary-700 hover:to-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200"
          >
            피드백 전송
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
          >
            취소
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// 성과 분석 모달 컴포넌트
function PerformanceModal({ mentee, onClose }: any) {
  // 멘티의 실제 성과 지표 데이터 사용
  const performanceData = [
    { skill: '은행업무', score: mentee.performance_scores?.banking || mentee.recent_score || 85 },
    { skill: '상품지식', score: mentee.performance_scores?.product_knowledge || mentee.recent_score || 78 },
    { skill: '고객응대', score: mentee.performance_scores?.customer_service || mentee.recent_score || 92 },
    { skill: '법규준수', score: mentee.performance_scores?.compliance || mentee.recent_score || 88 },
    { skill: 'IT활용', score: mentee.performance_scores?.it_usage || mentee.recent_score || 75 },
    { skill: '영업실적', score: mentee.performance_scores?.sales_performance || mentee.recent_score || 80 }
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl p-6 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-gray-900">
            {mentee.name}님 성과 분석
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <div className="grid lg:grid-cols-2 gap-6">
          {/* 레이더 차트 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4">종합 성과</h4>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={performanceData}>
                <PolarGrid stroke="#e5e7eb" strokeWidth={1} />
                <PolarAngleAxis 
                  dataKey="skill" 
                  tick={{ fontSize: 12, fill: '#374151' }}
                />
                <PolarRadiusAxis 
                  angle={90} 
                  domain={[0, 100]} 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                />
                <Radar
                  name="점수"
                  dataKey="score"
                  stroke="#d4a574"
                  fill="#d4a574"
                  fillOpacity={0.3}
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#d4a574' }}
                />
                <Tooltip 
                  formatter={(value: any) => [`${value}점`, '점수']}
                  labelFormatter={(label: string) => `지표: ${label}`}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          
          {/* 상세 점수 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4">지표별 상세</h4>
            <div className="space-y-3">
              {performanceData.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">{item.skill}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${item.score}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-bold text-gray-900 w-10 text-right">
                      {item.score}점
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            {/* 개선 제안 */}
            <div className="mt-6 p-4 bg-gradient-to-r from-amber-50 to-primary-50 rounded-xl border border-amber-200">
              <h5 className="font-semibold text-amber-800 mb-2 flex items-center">
                <LightBulbIcon className="w-5 h-5 mr-2" />
                개선 제안
              </h5>
              <ul className="text-sm text-amber-700 space-y-1">
                <li>• IT활용 능력 향상을 위한 교육 프로그램 참여</li>
                <li>• 상품지식 강화를 위한 정기 학습 계획 수립</li>
                <li>• 고객응대 우수 사례 공유 및 학습</li>
              </ul>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

// 피드백 카드 컴포넌트 (댓글 기능 포함)
function FeedbackCard({ feedback, index, currentTime }: any) {
  const { user } = useAuthStore()
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState<any[]>([])
  const [newComment, setNewComment] = useState('')
  const [isLoadingComments, setIsLoadingComments] = useState(false)
  
  const getDateBasedColor = (createdAt: string, colorSection?: string) => {
    // DB에 저장된 색상 섹션을 우선 사용
    if (colorSection) {
      switch (colorSection) {
        case 'red':
          return 'border-red-500 bg-red-50'
        case 'orange':
          return 'border-orange-500 bg-orange-50'
        case 'yellow':
          return 'border-yellow-500 bg-yellow-50'
        case 'gray':
          return 'border-gray-400 bg-gray-50'
        default:
          return 'border-gray-400 bg-gray-50'
      }
    }
    
    // 색상 섹션이 없으면 기존 시간 기반 계산 사용
    try {
      const now = new Date()
      const feedbackDate = new Date(createdAt)
      
      if (isNaN(feedbackDate.getTime())) {
        return 'border-gray-400 bg-gray-50'
      }
      
      const diffInHours = (now.getTime() - feedbackDate.getTime()) / (1000 * 60 * 60)
      
      if (diffInHours <= 24) {
        return 'border-red-500 bg-red-50'
      } else if (diffInHours <= 72) {
        return 'border-orange-500 bg-orange-50'
      } else if (diffInHours <= 168) {
        return 'border-yellow-500 bg-yellow-50'
      } else {
        return 'border-gray-400 bg-gray-50'
      }
    } catch (error) {
      console.error('색상 계산 오류:', error, createdAt)
      return 'border-gray-400 bg-gray-50'
    }
  }

  const getTimeLabel = (createdAt: string) => {
    try {
      // 항상 현재 시간을 새로 가져와서 계산
      const now = new Date()
      const feedbackDate = new Date(createdAt)
      
      // 유효한 날짜인지 확인
      if (isNaN(feedbackDate.getTime())) {
        console.error('Invalid date:', createdAt)
        return '시간 정보 없음'
      }
      
      const diffInMs = now.getTime() - feedbackDate.getTime()
      const diffInMinutes = diffInMs / (1000 * 60)
      const diffInHours = diffInMs / (1000 * 60 * 60)
      const diffInDays = diffInMs / (1000 * 60 * 60 * 24)
      
      // 디버깅 로그 (개발 환경에서만)
      if (process.env.NODE_ENV === 'development') {
        console.log('시간 계산 디버그:', {
          createdAt,
          now: now.toISOString(),
          feedbackDate: feedbackDate.toISOString(),
          diffInMs,
          diffInMinutes: Math.floor(diffInMinutes),
          diffInHours: Math.floor(diffInHours),
          diffInDays: Math.floor(diffInDays)
        })
      }
      
      if (diffInMinutes < 1) {
        return '방금 전'
      } else if (diffInMinutes < 60) {
        return `${Math.floor(diffInMinutes)}분 전`
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)}시간 전`
      } else if (diffInDays < 7) {
        return `${Math.floor(diffInDays)}일 전`
      } else {
        return feedbackDate.toLocaleDateString('ko-KR', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      }
    } catch (error) {
      console.error('시간 계산 오류:', error, createdAt)
      return '시간 계산 오류'
    }
  }

  const isRecent = () => {
    // 항상 현재 시간을 새로 가져와서 계산
    const now = new Date()
    const feedbackDate = new Date(feedback.created_at)
    const diffInHours = (now.getTime() - feedbackDate.getTime()) / (1000 * 60 * 60)
    return diffInHours <= 24
  }
  
  const loadComments = async () => {
    if (showComments && comments.length === 0) {
      setIsLoadingComments(true)
      try {
        const response = await dashboardAPI.getComments(feedback.id)
        setComments(response.comments || [])
      } catch (error) {
        console.error('댓글 로드 실패:', error)
      } finally {
        setIsLoadingComments(false)
      }
    }
  }
  
  const handleAddComment = async () => {
    if (!newComment.trim()) return
    
    try {
      await dashboardAPI.createComment(feedback.id, newComment)
      setNewComment('')
      // 댓글 목록 새로고침
      const response = await dashboardAPI.getComments(feedback.id)
      setComments(response.comments || [])
    } catch (error) {
      console.error('댓글 작성 실패:', error)
      alert('댓글 작성에 실패했습니다.')
    }
  }
  
  const handleDeleteComment = async (commentId: number) => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return
    
    try {
      await dashboardAPI.deleteComment(commentId)
      // 댓글 목록 새로고침
      const response = await dashboardAPI.getComments(feedback.id)
      setComments(response.comments || [])
    } catch (error) {
      console.error('댓글 삭제 실패:', error)
      alert('댓글 삭제에 실패했습니다.')
    }
  }
  
  useEffect(() => {
    if (showComments) {
      loadComments()
    }
  }, [showComments])

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className={`p-4 rounded-lg border-l-4 transition-all duration-300 hover:shadow-md ${
        feedback.is_read 
          ? 'bg-gray-50 border-gray-300' 
          : getDateBasedColor(feedback.created_at, feedback.color_section)
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              feedback.is_read ? 'bg-gray-400' : isRecent() ? 'bg-red-500' : 'bg-orange-500'
            }`}></div>
            <span className="text-sm font-medium text-gray-700">
              {feedback.mentor_name} 멘토
            </span>
          </div>
          <span className="text-xs text-gray-500">
            {getTimeLabel(feedback.created_at)}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {isRecent() && !feedback.is_read && (
            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full animate-pulse">
              최신 피드백
            </span>
          )}
        </div>
      </div>
      <p className="text-gray-800 leading-relaxed text-sm mb-3">{feedback.feedback_text}</p>
      
      {/* 댓글 토글 버튼 */}
        <button
          onClick={() => setShowComments(!showComments)}
          className="flex items-center space-x-2 text-sm text-primary-600 hover:text-primary-800 transition-colors"
        >
          <ChatBubbleLeftRightIcon className="w-4 h-4" />
          <span>{showComments ? '댓글 숨기기' : '댓글 보기'}</span>
          {comments.length > 0 && (
            <span className="px-2 py-0.5 bg-primary-100 text-primary-800 rounded-full text-xs">
              {comments.length}
            </span>
          )}
        </button>
      
      {/* 댓글 영역 */}
      {showComments && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {isLoadingComments ? (
            <div className="text-center text-gray-500 text-sm py-4">댓글 로딩 중...</div>
          ) : (
            <>
              {/* 댓글 목록 */}
              <div className="space-y-3 mb-4">
                {comments.map((comment: any) => (
                  <div key={comment.id} className="bg-white p-3 rounded-lg border border-gray-200">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs font-semibold ${
                          comment.user_role === 'MENTOR' ? 'text-primary-600' : 'text-amber-600'
                        }`}>
                          {comment.user_name}
                        </span>
                        <span className="text-xs text-gray-500">
                          {getTimeLabel(comment.created_at)}
                        </span>
                      </div>
                      {comment.user_id === user?.id && (
                        <button
                          onClick={() => handleDeleteComment(comment.id)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <p className="text-sm text-gray-700">{comment.comment_text}</p>
                  </div>
                ))}
                
                {comments.length === 0 && (
                  <p className="text-center text-gray-500 text-sm py-4">
                    아직 댓글이 없습니다. 첫 댓글을 남겨보세요!
                  </p>
                )}
              </div>
              
              {/* 댓글 작성 폼 */}
              <div className="flex items-start space-x-2">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="댓글을 입력하세요..."
                  className="flex-1 px-3 py-2 border border-primary-200 rounded-lg text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={2}
                />
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim()}
                  className="px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-lg hover:from-primary-700 hover:to-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-1"
                >
                  <PaperAirplaneIcon className="w-4 h-4" />
                  <span>전송</span>
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </motion.div>
  )
}

// 피드백 아코디언 컴포넌트
function FeedbackAccordion({ additionalFeedbacks, totalCount, currentTime }: any) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="border-t border-gray-200 pt-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 rounded-lg transition-colors"
      >
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">
            이전 피드백 {additionalFeedbacks.length}개 더 보기
          </span>
          <span className="text-xs text-gray-500">
            (총 {totalCount}개)
          </span>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </motion.div>
      </button>
      
      <motion.div
        initial={false}
        animate={{ 
          height: isExpanded ? 'auto' : 0,
          opacity: isExpanded ? 1 : 0
        }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="space-y-3 mt-3">
          {additionalFeedbacks.map((feedback: any, idx: number) => (
            <FeedbackCard 
              key={idx + 3} 
              feedback={feedback} 
              index={idx + 3}
              currentTime={currentTime}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

function StatCard({ icon: Icon, title, value, color }: any) {
  const colorClasses: any = {
    primary: 'from-primary-500 to-primary-600',
    amber: 'from-amber-500 to-amber-600',
    bank: 'from-bank-500 to-bank-600',
    accent: 'from-accent-500 to-accent-600',
  }

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-2xl p-6 text-white shadow-lg hover:shadow-xl transition-shadow`}>
      <Icon className="w-12 h-12 mb-4 opacity-80" />
      <p className="text-white/90 mb-1 font-medium">{title}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}



