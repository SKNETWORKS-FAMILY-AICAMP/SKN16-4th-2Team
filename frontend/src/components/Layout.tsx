/**
 * 레이아웃 컴포넌트
 * 네비게이션 바 및 전체 레이아웃
 */
import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { 
  HomeIcon, 
  DocumentTextIcon, 
  ChatBubbleBottomCenterIcon,
  ChartBarIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline'

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/home" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">M</span>
                </div>
                <span className="text-xl font-bold text-gray-900">멘토 시스템</span>
              </Link>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center space-x-1">
              <NavLink to="/home" icon={HomeIcon} text="홈" />
              <NavLink to="/documents" icon={DocumentTextIcon} text="자료실" />
              <NavLink to="/board" icon={ChatBubbleBottomCenterIcon} text="대나무숲" />
              <NavLink to="/dashboard" icon={ChartBarIcon} text="대시보드" />
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">

              <button
                className="flex items-center space-x-2 focus:outline-none"
                onClick={() => navigate('/mypage')}
                title="마이페이지로 이동"
              >
                {user?.photo_url ? (
                  <img src={user.photo_url} alt={user.name} className="w-8 h-8 rounded-full" />
                ) : (
                  <UserCircleIcon className="w-8 h-8 text-gray-400" />
                )}
                <div className="hidden md:block text-sm text-left">
                  <div className="font-medium text-gray-900">{user?.name}</div>
                  <div className="text-gray-500 text-xs">
                    {user?.role === 'admin' && '관리자'}
                    {user?.role === 'mentor' && '멘토'}
                    {user?.role === 'mentee' && '멘티'}
                  </div>
                </div>
              </button>
              
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
                <span className="hidden md:inline text-sm">로그아웃</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}

function NavLink({ to, icon: Icon, text }: { to: string; icon: any; text: string }) {
  return (
    <Link
      to={to}
      className="flex items-center space-x-2 px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
    >
      <Icon className="w-5 h-5" />
      <span className="hidden md:inline text-sm font-medium">{text}</span>
    </Link>
  )
}



