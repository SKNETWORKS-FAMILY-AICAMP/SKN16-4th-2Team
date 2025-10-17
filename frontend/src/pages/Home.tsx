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
        className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-8 text-white"
      >
        <h1 className="text-3xl font-bold mb-2">
          안녕하세요, {user?.name}님! 👋
        </h1>
        <p className="text-primary-100 text-lg">
          {user?.role === 'mentee' && '오늘도 성장하는 하루 되세요!'}
          {user?.role === 'mentor' && '멘티들을 위한 조언을 준비해보세요.'}
          {user?.role === 'admin' && '시스템을 관리해주세요.'}
        </p>
      </motion.div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <QuickLinkCard
          to="/documents"
          icon={DocumentTextIcon}
          title="자료실"
          description="업무 관련 문서 및 자료"
          color="blue"
        />
        <QuickLinkCard
          to="/board"
          icon={ChatBubbleBottomCenterIcon}
          title="대나무숲"
          description="익명 게시판"
          color="green"
        />
        <QuickLinkCard
          to="/dashboard"
          icon={ChartBarIcon}
          title="대시보드"
          description="학습 현황 및 통계"
          color="purple"
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
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">최근 활동</h2>
        <div className="space-y-4">
          <ActivityItem
            title="시스템에 오신 것을 환영합니다!"
            description="AI 챗봇으로 궁금한 점을 물어보세요."
            time="방금 전"
          />
          <ActivityItem
            title="자료실을 확인하세요"
            description="업무에 필요한 모든 자료가 준비되어 있습니다."
            time="1분 전"
          />
          <ActivityItem
            title="대시보드에서 학습 현황을 확인하세요"
            description="나의 성장 과정을 한눈에 볼 수 있습니다."
            time="5분 전"
          />
        </div>
      </div>

      {/* Tips */}
      {user?.role === 'mentee' && (
        <div className="bg-primary-50 border border-primary-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-primary-900 mb-3">💡 Tip</h3>
          <ul className="space-y-2 text-primary-800">
            <li>• AI 챗봇에게 업무 관련 질문을 자유롭게 해보세요</li>
            <li>• 자료실에서 필요한 문서를 검색할 수 있습니다</li>
            <li>• 대나무숲에서 익명으로 고민을 나눌 수 있습니다</li>
            <li>• 대시보드에서 학습 진행도를 확인하세요</li>
          </ul>
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
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
  }

  return (
    <Link
      to={to}
      className={`bg-gradient-to-br ${colorClasses[color]} rounded-xl p-6 text-white hover:shadow-lg transition-shadow`}
    >
      <Icon className="w-12 h-12 mb-4" />
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-white/80">{description}</p>
    </Link>
  )
}

function ActivityItem({ title, description, time }: any) {
  return (
    <div className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
      <div className="w-2 h-2 bg-primary-600 rounded-full mt-2"></div>
      <div className="flex-1">
        <h4 className="font-semibold text-gray-900">{title}</h4>
        <p className="text-gray-600 text-sm">{description}</p>
        <span className="text-gray-400 text-xs">{time}</span>
      </div>
    </div>
  )
}


