/**
 * 랜딩 페이지
 * 로그인 전 프로젝트 소개
 */
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  ChatBubbleLeftRightIcon, 
  DocumentTextIcon, 
  UserGroupIcon,
  ChartBarIcon,
  SparklesIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-100">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              은행 신입사원을 위한
              <br />
              <span className="bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
                AI 멘토 시스템
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              RAG 기반 지능형 챗봇과 함께 빠르게 성장하세요.
              <br />
              멘토의 지식을 체계화하여 언제든 필요한 정보를 얻을 수 있습니다.
            </p>
            <div className="flex justify-center space-x-4">
              <Link
                to="/register"
                className="px-8 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors shadow-lg"
              >
                시작하기
              </Link>
              <Link
                to="/login"
                className="px-8 py-3 bg-white text-primary-600 rounded-lg font-semibold hover:bg-gray-50 transition-colors border-2 border-primary-600"
              >
                로그인
              </Link>
            </div>
          </motion.div>

          {/* Floating Animation */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 1 }}
            className="mt-16 relative"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-96 h-96 bg-primary-200 rounded-full filter blur-3xl opacity-30 animate-pulse"></div>
            </div>
            <div className="relative bg-white rounded-2xl shadow-2xl p-8 max-w-3xl mx-auto">
              <img
                src="https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&h=400&fit=crop"
                alt="Team collaboration"
                className="rounded-lg w-full h-64 object-cover"
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          주요 기능
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon={ChatBubbleLeftRightIcon}
            title="AI 챗봇"
            description="RAG 기반 지능형 챗봇이 24/7 궁금한 점을 해결해드립니다."
            color="primary"
          />
          <FeatureCard
            icon={DocumentTextIcon}
            title="자료실"
            description="은행업무 관련 모든 문서와 자료를 한 곳에서 관리합니다."
            color="blue"
          />
          <FeatureCard
            icon={UserGroupIcon}
            title="멘토링"
            description="전담 멘토가 배정되어 체계적인 온보딩을 지원합니다."
            color="green"
          />
          <FeatureCard
            icon={LockClosedIcon}
            title="익명 게시판"
            description="대나무숲에서 부담 없이 질문하고 소통할 수 있습니다."
            color="purple"
          />
          <FeatureCard
            icon={ChartBarIcon}
            title="학습 분석"
            description="시험 점수와 학습 진행도를 시각화하여 확인할 수 있습니다."
            color="orange"
          />
          <FeatureCard
            icon={SparklesIcon}
            title="맞춤형 지원"
            description="개인별 학습 패턴을 분석하여 최적의 학습 경로를 제안합니다."
            color="pink"
          />
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            지금 바로 시작하세요
          </h2>
          <p className="text-primary-100 mb-8 text-lg">
            은행 신입사원의 성공적인 시작을 AI 멘토가 함께합니다.
          </p>
          <Link
            to="/register"
            className="inline-block px-8 py-3 bg-white text-primary-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors shadow-lg"
          >
            무료로 시작하기
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2024 Bank Mentor System. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, description, color }: any) {
  const colorClasses: any = {
    primary: 'bg-primary-100 text-primary-600',
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
    pink: 'bg-pink-100 text-pink-600',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      viewport={{ once: true }}
      className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow"
    >
      <div className={`w-12 h-12 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </motion.div>
  )
}


