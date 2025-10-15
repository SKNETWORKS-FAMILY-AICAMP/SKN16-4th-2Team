/**
 * 로그인 페이지
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../utils/api'
import { LockClosedIcon } from '@heroicons/react/24/solid'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // 1. 로그인 API 호출하여 토큰 받기
      const data = await authAPI.login(email, password)
      
      // 2. 토큰을 먼저 임시로 스토어에 저장 (API 인터셉터가 사용할 수 있도록)
      login(data.access_token, data.refresh_token, {
        id: 0,
        email: email,
        name: '',
        role: 'mentee' as any,
      })
      
      // 3. 이제 토큰이 저장되었으므로 사용자 정보 가져오기
      const userData = await authAPI.getCurrentUser()
      
      // 4. 완전한 사용자 정보로 업데이트
      login(data.access_token, data.refresh_token, userData)
      
      // 5. 홈으로 이동
      navigate('/home')
    } catch (err: any) {
      console.error('Login error:', err)
      let errorMessage = '로그인에 실패했습니다.'
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      } else if (err.code === 'NETWORK_ERROR' || err.code === 'ECONNREFUSED') {
        errorMessage = '서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.'
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl mb-4">
            <LockClosedIcon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">로그인</h2>
          <p className="text-gray-600 mt-2">멘토 시스템에 오신 것을 환영합니다</p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                이메일
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '로그인 중...' : '로그인'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              계정이 없으신가요?{' '}
              <Link to="/register" className="text-primary-600 font-semibold hover:text-primary-700">
                회원가입
              </Link>
            </p>
          </div>
        </div>

        {/* Demo Accounts */}
        <div className="mt-6 bg-white rounded-lg p-4 text-sm text-gray-600">
          <p className="font-semibold mb-2">테스트 계정:</p>
          <ul className="space-y-1">
            <li>• 관리자: admin@bank.com / admin123</li>
            <li>• 멘토: mentor@bank.com / mentor123</li>
            <li>• 멘티: mentee@bank.com / mentee123</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

