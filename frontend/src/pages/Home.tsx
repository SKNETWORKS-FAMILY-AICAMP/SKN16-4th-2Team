/**
 * 홈 페이지
 * 로그인 후 메인 화면
 */
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { motion } from 'framer-motion'
import {
  DocumentTextIcon,
  ChatBubbleBottomCenterIcon,
  ChartBarIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import ChatBot from '../components/ChatBot'

export default function Home() {
  const { user } = useAuthStore()
  const [isChatBotOpen, setIsChatBotOpen] = useState(false)

  const handleOpenChatBot = () => {
    setIsChatBotOpen(true)
  }

  const handleCloseChatBot = () => {
    setIsChatBotOpen(false)
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-primary-600 via-primary-500 to-amber-500 rounded-3xl p-8 text-white relative overflow-hidden shadow-2xl"
      >
        
        <div className="relative z-10">
          <div className="flex items-center mb-6">
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
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4">
            <p className="text-white/90 text-lg">
              {user?.role === 'mentee' && '하경곰과 함께 성장하는 멋진 하루 되세요! 🌟'}
              {user?.role === 'mentor' && '신입사원들의 성공적인 온보딩을 위해 함께해주세요. 💪'}
              {user?.role === 'admin' && '온보딩 플랫폼을 효율적으로 관리해주세요. ⚙️'}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <QuickLinkCard
          to="/documents"
          icon={DocumentTextIcon}
          title="스마트 자료실"
          description="업무 관련 문서 및 학습 자료"
          color="bank"
        />
        <QuickLinkCard
          to="/board"
          icon={ChatBubbleBottomCenterIcon}
          title="소통공간"
          description="익명으로 소통하는 안전한 공간"
          color="primary"
        />
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
          <h3 className="text-xl font-semibold mb-2">AI 챗봇</h3>
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
            title="스마트 자료실 탐방하기"
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
                스마트 자료실에서 필요한 문서를 검색할 수 있습니다
              </li>
            </ul>
            <ul className="space-y-3 text-primary-700">
              <li className="flex items-start">
                <span className="text-amber-500 mr-2">💬</span>
                소통공간에서 익명으로 고민을 나눌 수 있습니다
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


