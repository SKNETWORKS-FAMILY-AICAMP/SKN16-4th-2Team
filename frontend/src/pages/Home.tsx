/**
 * 홈 페이지
 * 로그인 후 메인 화면
 */
import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { motion } from 'framer-motion'
import {
  DocumentTextIcon,
  ChatBubbleBottomCenterIcon,
  ChartBarIcon,
  SparklesIcon,
  EyeIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import ChatBot from '../components/ChatBot'
import { documentAPI, postAPI } from '../utils/api'

export default function Home() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [isChatBotOpen, setIsChatBotOpen] = useState(false)
  const [recentDocuments, setRecentDocuments] = useState([])
  const [popularPosts, setPopularPosts] = useState([])
  const [loading, setLoading] = useState(true)

  const handleOpenChatBot = () => {
    setIsChatBotOpen(true)
  }

  const handleCloseChatBot = () => {
    setIsChatBotOpen(false)
  }

  const handleDocumentClick = () => {
    navigate('/documents')
  }

  const handlePostClick = (postId: number) => {
    navigate(`/board/${postId}`)
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [documentsResponse, postsResponse] = await Promise.all([
          documentAPI.getRecentDocuments(3),
          postAPI.getPopularPosts(3)
        ])
        setRecentDocuments(documentsResponse)
        setPopularPosts(postsResponse)
      } catch (error) {
        console.error('Failed to fetch home data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-primary-600 via-primary-500 to-amber-500 rounded-3xl p-8 text-white relative overflow-hidden shadow-2xl"
      >
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <img src="/assets/bear.png" alt="하경곰" className="w-20 h-20 mr-6 rounded-full shadow-lg" />
              <div>
                <h1 className="text-4xl font-bold mb-2">
                  안녕하세요, {user?.name}님! 🐻
                </h1>
                <p className="text-white/90 text-xl font-medium">
                  하경은행 스마트 온보딩 플랫폼에 오신 것을 환영합니다
                </p>
              </div>
            </div>
            {/* 개발용 테스트 버튼 */}
            {import.meta.env.DEV && (
              <button
                onClick={() => navigate('/simulation-feedback')}
                className="bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
              >
                📊 피드백 미리보기
              </button>
            )}
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4">
            <p className="text-white/90 text-lg">
              {user?.role === 'mentee' && '하경곰과 함께 성장하는 멋진 하루 되세요! 🌟'}
              {user?.role === 'mentor' && '신입사원들의 성공적인 온보딩을 위해 함께해주세요. 💪'}
              {user?.role === 'admin' && '온보딩 플랫폼을 효율적으로 관리해주세요. ⚙️'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* 자료실 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <DocumentTextIcon className="w-8 h-8 text-bank-600 mr-3" />
            <h2 className="text-2xl font-bold text-bank-800">자료실</h2>
          </div>
          <button
            onClick={handleDocumentClick}
            className="text-bank-600 hover:text-bank-700 font-medium flex items-center"
          >
            전체보기
            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
        
        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : recentDocuments.length > 0 ? (
          <div className="space-y-4">
            {recentDocuments.map((doc: any) => (
              <div
                key={doc.id}
                onClick={handleDocumentClick}
                className="p-4 bg-gradient-to-r from-bank-50 to-primary-50 rounded-xl border border-bank-100 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-bank-800 group-hover:text-bank-900 mb-1">
                      {doc.title}
                    </h4>
                    <p className="text-bank-600 text-sm mb-2">{doc.description || '설명 없음'}</p>
                    <div className="flex items-center text-xs text-bank-500">
                      <CalendarIcon className="w-3 h-3 mr-1" />
                      {new Date(doc.upload_date).toLocaleDateString('ko-KR')}
                      <span className="mx-2">•</span>
                      <span>{doc.category}</span>
                    </div>
                  </div>
                  <DocumentTextIcon className="w-6 h-6 text-bank-400 group-hover:text-bank-600 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>최근 업로드된 자료가 없습니다.</p>
          </div>
        )}
      </motion.div>

      {/* 대나무숲 섹션 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <ChatBubbleBottomCenterIcon className="w-8 h-8 text-primary-600 mr-3" />
            <h2 className="text-2xl font-bold text-primary-800">대나무숲</h2>
          </div>
          <Link
            to="/board"
            className="text-primary-600 hover:text-primary-700 font-medium flex items-center"
          >
            전체보기
            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
        
        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : popularPosts.length > 0 ? (
          <div className="space-y-4">
            {popularPosts.map((post: any) => (
              <div
                key={post.id}
                onClick={() => handlePostClick(post.id)}
                className="p-4 bg-gradient-to-r from-primary-50 to-amber-50 rounded-xl border border-primary-100 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-primary-800 group-hover:text-primary-900 mb-1">
                      {post.title}
                    </h4>
                    <p className="text-primary-600 text-sm mb-2 line-clamp-2">{post.content}</p>
                    <div className="flex items-center text-xs text-primary-500">
                      <EyeIcon className="w-3 h-3 mr-1" />
                      {post.view_count}회 조회
                      <span className="mx-2">•</span>
                      <CalendarIcon className="w-3 h-3 mr-1" />
                      {new Date(post.created_at).toLocaleDateString('ko-KR')}
                    </div>
                  </div>
                  <ChatBubbleBottomCenterIcon className="w-6 h-6 text-primary-400 group-hover:text-primary-600 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <ChatBubbleBottomCenterIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>최근 인기 게시물이 없습니다.</p>
          </div>
        )}
      </motion.div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-2 gap-6">
        <QuickLinkCard
          to="/dashboard"
          icon={ChartBarIcon}
          title="성장현황"
          description="학습 진행도 및 성과 분석"
          color="amber"
        />
        <div 
          onClick={handleOpenChatBot}
          className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white cursor-pointer hover:shadow-lg transition-all hover:scale-105"
        >
          <SparklesIcon className="w-12 h-12 mb-4" />
          <h3 className="text-xl font-semibold mb-2">AI 하리보</h3>
          <p className="text-orange-100">클릭하여 챗봇 시작하기</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-primary-100">
        <div className="flex items-center mb-6">
          <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
          <h2 className="text-2xl font-bold text-bank-800">최근 활동</h2>
        </div>
        <div className="space-y-4">
          <ActivityItem
            title="AI 하리보와 함께하는 온보딩 시작!"
            description="AI 챗봇으로 궁금한 점을 자유롭게 물어보세요."
            time="방금 전"
          />
          <ActivityItem
            title="자료실 탐방하기"
            description="업무에 필요한 모든 학습 자료가 체계적으로 정리되어 있습니다."
            time="1분 전"
          />
          <ActivityItem
            title="성장현황에서 나의 발전 확인하기"
            description="개인별 학습 진행도와 성과를 한눈에 볼 수 있습니다."
            time="5분 전"
          />
        </div>
      </div>

      {/* Tips */}
      {user?.role === 'mentee' && (
        <div className="bg-gradient-to-r from-primary-50 to-amber-50 border border-primary-200 rounded-2xl p-8">
          <h3 className="text-xl font-bold text-primary-800 mb-4 flex items-center">
            <img src="/assets/bear.png" alt="하경곰" className="w-8 h-8 mr-3 rounded-full" />
            하경곰의 온보딩 플랫폼 활용 가이드
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <ul className="space-y-3 text-primary-700">
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">🤖</span>
                AI 하리보에게 업무 관련 질문을 자유롭게 해보세요
              </li>
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">📚</span>
                자료실에서 필요한 문서를 검색할 수 있습니다
              </li>
            </ul>
            <ul className="space-y-3 text-primary-700">
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">💬</span>
                대나무숲에서 익명으로 고민을 나눌 수 있습니다
              </li>
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">📊</span>
                성장현황에서 학습 진행도를 확인하세요
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* ChatBot */}
      <ChatBot 
        forceOpen={isChatBotOpen} 
        onClose={handleCloseChatBot}
      />
    </div>
  )
}

function QuickLinkCard({ to, icon: Icon, title, description, color }: any) {
  const colorClasses: any = {
    bank: 'from-bank-500 to-bank-600',
    primary: 'from-primary-500 to-primary-600',
    amber: 'from-amber-500 to-amber-600',
    accent: 'from-accent-500 to-accent-600',
  }

  return (
    <Link
      to={to}
      className={`bg-gradient-to-br ${colorClasses[color]} rounded-2xl p-6 text-white hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 group`}
    >
      <Icon className="w-12 h-12 mb-4 group-hover:scale-110 transition-transform" />
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-white/90">{description}</p>
    </Link>
  )
}

function ActivityItem({ title, description, time }: any) {
  return (
    <div className="flex items-start space-x-4 p-4 bg-gradient-to-r from-primary-50 to-amber-50 rounded-xl border border-primary-100 hover:shadow-md transition-shadow">
      <div className="w-3 h-3 bg-gradient-to-r from-primary-500 to-amber-500 rounded-full mt-2 shadow-sm"></div>
      <div className="flex-1">
        <h4 className="font-bold text-bank-800 mb-1">{title}</h4>
        <p className="text-primary-700 text-sm mb-2">{description}</p>
        <span className="text-primary-500 text-xs font-medium">{time}</span>
      </div>
    </div>
  )
}


