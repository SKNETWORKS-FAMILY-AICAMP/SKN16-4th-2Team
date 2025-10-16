/**
 * 아이디(이메일) 찾기 페이지
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authAPI } from '../utils/api'
import { EnvelopeIcon, UserIcon, IdentificationIcon } from '@heroicons/react/24/outline'

export default function FindId() {
  const [name, setName] = useState('')
  const [employeeNumber, setEmployeeNumber] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [foundEmail, setFoundEmail] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setFoundEmail(null)

    try {
      const data = await authAPI.findId(name, employeeNumber)
      setFoundEmail(data.email)
    } catch (err: any) {
      console.error('Find ID error:', err)
      let errorMessage = '아이디 찾기에 실패했습니다.'
      
      if (err.response?.data?.detail) {
        if (err.response.data.detail === 'User not found with provided information') {
          errorMessage = '입력하신 정보와 일치하는 사용자를 찾을 수 없습니다.'
        } else {
          errorMessage = err.response.data.detail
        }
      } else if (err.message) {
        errorMessage = err.message
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
            <EnvelopeIcon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">아이디 찾기</h2>
          <p className="text-gray-600 mt-2">이름과 사원번호를 입력해주세요</p>
        </div>

        {/* Find ID Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {foundEmail ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 font-semibold mb-3">아이디를 찾았습니다!</p>
                <p className="text-xl font-mono font-semibold text-gray-900">{foundEmail}</p>
              </div>
              
              <div className="flex gap-3">
                <Link
                  to="/login"
                  className="flex-1 py-3 bg-primary-600 text-white rounded-lg font-semibold text-center hover:bg-primary-700 transition-colors"
                >
                  로그인하기
                </Link>
                <Link
                  to="/find-password"
                  className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold text-center hover:bg-gray-200 transition-colors"
                >
                  비밀번호 찾기
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <UserIcon className="w-4 h-4" />
                    이름
                  </div>
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="홍길동"
                />
              </div>

              <div>
                <label htmlFor="employee_number" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <IdentificationIcon className="w-4 h-4" />
                    사원번호
                  </div>
                </label>
                <input
                  id="employee_number"
                  name="employee_number"
                  type="text"
                  required
                  value={employeeNumber}
                  onChange={(e) => setEmployeeNumber(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="EMP12345"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '검색 중...' : '아이디 찾기'}
              </button>
            </form>
          )}

          <div className="mt-6 text-center space-y-2">
            <Link to="/login" className="block text-sm text-gray-600 hover:text-primary-600">
              로그인으로 돌아가기
            </Link>
            <Link to="/find-password" className="block text-sm text-gray-600 hover:text-primary-600">
              비밀번호 찾기
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

