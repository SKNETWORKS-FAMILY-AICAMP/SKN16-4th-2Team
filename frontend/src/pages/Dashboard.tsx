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
  ChatBubbleBottomCenterTextIcon,
  TrophyIcon
} from '@heroicons/react/24/outline'
import { 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts'
import { motion } from 'framer-motion'

export default function Dashboard() {
  const { user } = useAuthStore()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [user])

  const loadDashboard = async () => {
    try {
      setLoading(true)
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
    return <MenteeDashboard data={data} />
  } else if (user?.role === 'mentor' || user?.role === 'admin') {
    return <MentorDashboard data={data} />
  }

  return null
}

function MenteeDashboard({ data }: any) {
  // 시험 점수를 레이더 차트 데이터로 변환
  const radarData = data?.exam_scores?.[0]?.score_data
    ? Object.entries(data.exam_scores[0].score_data).map(([subject, score]) => ({
        subject,
        score,
      }))
    : []

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">내 대시보드</h1>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-6">
        <StatCard
          icon={ChatBubbleBottomCenterTextIcon}
          title="총 대화 수"
          value={data?.learning_progress?.total_chats || 0}
          color="blue"
        />
        <StatCard
          icon={AcademicCapIcon}
          title="학습 진행도"
          value={`${data?.learning_progress?.progress_percentage || 0}%`}
          color="green"
        />
        <StatCard
          icon={TrophyIcon}
          title="최근 시험 점수"
          value={data?.exam_scores?.[0]?.total_score?.toFixed(1) || 'N/A'}
          color="purple"
        />
      </div>

      {/* Mentor Info */}
      {data?.mentor_info && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-md p-6"
        >
          <h2 className="text-xl font-bold text-gray-900 mb-4">담당 멘토</h2>
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
                <div className="mt-3 p-3 bg-primary-50 rounded-lg">
                  <p className="text-primary-900 text-sm italic">
                    "{data.mentor_info.encouragement_message}"
                  </p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Exam Scores - Radar Chart */}
      {radarData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-md p-6"
        >
          <h2 className="text-xl font-bold text-gray-900 mb-4">시험 성적 분석</h2>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar
                name="점수"
                dataKey="score"
                stroke="#0ea5e9"
                fill="#0ea5e9"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Recent Chats */}
      {data?.recent_chats && data.recent_chats.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-md p-6"
        >
          <h2 className="text-xl font-bold text-gray-900 mb-4">최근 대화</h2>
          <div className="space-y-4">
            {data.recent_chats.slice(0, 5).map((chat: any, idx: number) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                <p className="font-medium text-gray-900 mb-1">{chat.user_message}</p>
                <p className="text-sm text-gray-600 line-clamp-2">{chat.bot_response}</p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}

function MentorDashboard({ data }: any) {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">멘토 대시보드</h1>

      {/* Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <StatCard
          icon={UserIcon}
          title="담당 멘티"
          value={data?.mentees?.length || 0}
          color="blue"
        />
        <StatCard
          icon={ChatBubbleBottomCenterTextIcon}
          title="자주 묻는 질문"
          value={data?.frequent_questions?.length || 0}
          color="green"
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
          color="purple"
        />
      </div>

      {/* Mentees List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-md p-6"
      >
        <h2 className="text-xl font-bold text-gray-900 mb-4">담당 멘티 목록</h2>
        <div className="space-y-4">
          {data?.mentees?.map((mentee: any) => (
            <div key={mentee.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-4">
                {mentee.photo_url ? (
                  <img src={mentee.photo_url} alt={mentee.name} className="w-12 h-12 rounded-full" />
                ) : (
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    <UserIcon className="w-6 h-6 text-primary-600" />
                  </div>
                )}
                <div>
                  <h3 className="font-semibold text-gray-900">{mentee.name}</h3>
                  <p className="text-sm text-gray-600">
                    {mentee.team} • MBTI: {mentee.mbti}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">최근 점수</p>
                <p className="text-lg font-bold text-primary-600">
                  {mentee.recent_score?.toFixed(1) || 'N/A'}
                </p>
              </div>
            </div>
          ))}
          {(!data?.mentees || data.mentees.length === 0) && (
            <p className="text-center text-gray-500 py-8">담당 멘티가 없습니다</p>
          )}
        </div>
      </motion.div>

      {/* Frequent Questions */}
      {data?.frequent_questions && data.frequent_questions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-md p-6"
        >
          <h2 className="text-xl font-bold text-gray-900 mb-4">자주 묻는 질문 키워드</h2>
          <div className="flex flex-wrap gap-2">
            {data.frequent_questions.slice(0, 20).map((item: any, idx: number) => (
              <span
                key={idx}
                className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
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

function StatCard({ icon: Icon, title, value, color }: any) {
  const colorClasses: any = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
  }

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-xl p-6 text-white`}>
      <Icon className="w-12 h-12 mb-4 opacity-80" />
      <p className="text-white/80 mb-1">{title}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  )
}


