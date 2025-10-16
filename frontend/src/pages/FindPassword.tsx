/**
 * 비밀번호 찾기 페이지
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authAPI } from '../utils/api'
import { KeyIcon, EnvelopeIcon, IdentificationIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'

export default function FindPassword() {
  const [step, setStep] = useState<'verify' | 'reset' | 'success'>('verify')
  
  // Step 1: 본인 확인
  const [email, setEmail] = useState('')
  const [employeeNumber, setEmployeeNumber] = useState('')
  
  // Step 2: 새 비밀번호 설정
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (!email || !employeeNumber) {
      setError('이메일과 사원번호를 모두 입력해주세요.')
      return
    }
    
    // 다음 단계로 이동 (본인 확인은 비밀번호 재설정 시 함께 처리)
    setStep('reset')
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // 비밀번호 검증
    if (newPassword.length < 6) {
      setError('비밀번호는 최소 6자 이상이어야 합니다.')
      setLoading(false)
      return
    }

    if (newPassword !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      setLoading(false)
      return
    }

    try {
      await authAPI.resetPassword(email, employeeNumber, newPassword)
      setStep('success')
    } catch (err: any) {
      console.error('Reset password error:', err)
      let errorMessage = '비밀번호 재설정에 실패했습니다.'
      
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
            <KeyIcon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">비밀번호 찾기</h2>
          <p className="text-gray-600 mt-2">
            {step === 'verify' && '본인 확인을 위해 정보를 입력해주세요'}
            {step === 'reset' && '새로운 비밀번호를 설정해주세요'}
            {step === 'success' && '비밀번호가 성공적으로 변경되었습니다'}
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {/* Step 1: 본인 확인 */}
          {step === 'verify' && (
            <form onSubmit={handleVerify} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <EnvelopeIcon className="w-4 h-4" />
                    이메일
                  </div>
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
                className="w-full py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
              >
                다음
              </button>
            </form>
          )}

          {/* Step 2: 새 비밀번호 설정 */}
          {step === 'reset' && (
            <form onSubmit={handleResetPassword} className="space-y-6">
              <div>
                <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <KeyIcon className="w-4 h-4" />
                    새 비밀번호
                  </div>
                </label>
                <div className="relative">
                  <input
                    id="new_password"
                    name="new_password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="새 비밀번호 (최소 6자)"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="w-5 h-5 text-gray-600" />
                    ) : (
                      <EyeIcon className="w-5 h-5 text-gray-600" />
                    )}
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
                  <div className="flex items-center gap-2">
                    <KeyIcon className="w-4 h-4" />
                    비밀번호 확인
                  </div>
                </label>
                <div className="relative">
                  <input
                    id="confirm_password"
                    name="confirm_password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="비밀번호 확인"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="w-5 h-5 text-gray-600" />
                    ) : (
                      <EyeIcon className="w-5 h-5 text-gray-600" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep('verify')}
                  className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                >
                  이전
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? '처리 중...' : '비밀번호 변경'}
                </button>
              </div>
            </form>
          )}

          {/* Success Message */}
          {step === 'success' && (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
                <p className="text-green-800 font-semibold mb-2">✓ 비밀번호가 변경되었습니다!</p>
                <p className="text-sm text-gray-600">새 비밀번호로 로그인해주세요.</p>
              </div>
              
              <Link
                to="/login"
                className="block w-full py-3 bg-primary-600 text-white rounded-lg font-semibold text-center hover:bg-primary-700 transition-colors"
              >
                로그인하기
              </Link>
            </div>
          )}

          {step !== 'success' && (
            <div className="mt-6 text-center space-y-2">
              <Link to="/login" className="block text-sm text-gray-600 hover:text-primary-600">
                로그인으로 돌아가기
              </Link>
              <Link to="/find-id" className="block text-sm text-gray-600 hover:text-primary-600">
                아이디 찾기
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
