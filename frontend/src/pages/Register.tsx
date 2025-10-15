/**
 * 회원가입 페이지
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authAPI } from '../utils/api'
import { UserPlusIcon } from '@heroicons/react/24/solid'

export default function Register() {
  const interestOptions = [
    'IT/테크',
    '주식',
    '부동산',
    '디자인/예술',
    '공연/전시',
    '마케팅',
    '스포츠',
    '음악',
    '독서',
    '게임',
    '사내 소모임',
    '자기계발'
  ]

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    role: 'mentee',
    phone: '',
    extension: '',
    emergency_contact: '',
    interests: [],
    team: '',
    team_number: '',
    employee_number: '',
    join_year: '',
    position: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showInterests, setShowInterests] = useState(false)
  
  const navigate = useNavigate()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  const handleInterestToggle = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }

    // 관심사 3개 이상 선택 확인
    if (formData.interests.length < 3) {
      setError('관심사를 3개 이상 선택해주세요.')
      return
    }

    setLoading(true)

    try {
      // 회원가입 API 호출
      await authAPI.register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        role: formData.role,
        phone: formData.phone || undefined,
        extension: formData.extension || undefined,
        emergency_contact: formData.emergency_contact || undefined,
        interests: JSON.stringify(formData.interests),
        team: formData.team || undefined,
        team_number: formData.team_number || undefined,
        employee_number: formData.employee_number || undefined,
        join_year: formData.join_year ? parseInt(formData.join_year) : undefined,
        position: formData.position || undefined,
      })
      
      // 성공 시 로그인 페이지로 이동
      navigate('/login')
    } catch (err: any) {
      console.error('Register error:', err)
      setError(err.response?.data?.detail || '회원가입에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 px-4 py-12">
      <div className="max-w-2xl w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-700 rounded-2xl mb-4">
            <UserPlusIcon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">회원가입</h2>
          <p className="text-gray-600 mt-2">멘토 시스템에 가입하세요</p>
        </div>

        {/* Register Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Email */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이메일 *
                </label>
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="your@email.com"
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호 *
                </label>
                <input
                  type="password"
                  name="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호 확인 *
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="••••••••"
                />
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  이름 *
                </label>
                <input
                  type="text"
                  name="name"
                  autoComplete="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="홍길동"
                />
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  역할 *
                </label>
                <select
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="mentee">멘티 (신입사원)</option>
                  <option value="mentor">멘토</option>
                  <option value="admin">관리자</option>
                </select>
              </div>

              {/* 사원번호 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  사원번호 *
                </label>
                <input
                  type="text"
                  name="employee_number"
                  required
                  value={formData.employee_number}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="2024001"
                />
              </div>

              {/* 입사년도 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  입사년도
                </label>
                <input
                  type="text"
                  name="join_year"
                  value={formData.join_year}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="2024"
                />
              </div>

              {/* 직책 */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  직책
                </label>
                <select
                  name="position"
                  value={formData.position}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">선택하세요</option>
                  <option value="사원">사원</option>
                  <option value="주임">주임</option>
                  <option value="대리">대리</option>
                  <option value="과장">과장</option>
                  <option value="차장">차장</option>
                  <option value="부장">부장</option>
                  <option value="임원">임원</option>
                  <option value="기타">기타</option>
                </select>
              </div>

              {/* 내선번호 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  내선번호 *
                </label>
                <input
                  type="text"
                  name="extension"
                  required
                  value={formData.extension}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="1234"
                />
              </div>

              {/* 비상 연락망 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  비상 연락망 *
                </label>
                <input
                  type="tel"
                  name="emergency_contact"
                  autoComplete="tel"
                  required
                  value={formData.emergency_contact}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="010-1234-5678"
                />
              </div>

              {/* 부서 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  부서
                </label>
                <select
                  name="team"
                  value={formData.team}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">선택하세요</option>
                  <option value="영업부">영업부</option>
                  <option value="기업금융 / 기업영업부">기업금융 / 기업영업부</option>
                  <option value="리스크관리부">리스크관리부</option>
                  <option value="여신심사 / 여신관리부">여신심사 / 여신관리부</option>
                  <option value="자금부 / 자금시장부">자금부 / 자금시장부</option>
                  <option value="재무 / 회계부">재무 / 회계부</option>
                  <option value="기획 / 전략부">기획 / 전략부</option>
                  <option value="IT / 정보기술부">IT / 정보기술부</option>
                  <option value="디지털 / 혁신부서">디지털 / 혁신부서</option>
                  <option value="마케팅 / 홍보부">마케팅 / 홍보부</option>
                  <option value="고객지원 / 고객센터 / 민원부">고객지원 / 고객센터 / 민원부</option>
                  <option value="법무부">법무부</option>
                  <option value="감사 / 내부감사부">감사 / 내부감사부</option>
                  <option value="보안 / 정보보호부">보안 / 정보보호부</option>
                  <option value="소비자보호부">소비자보호부</option>
                  <option value="상품 / 금융상품개발부">상품 / 금융상품개발부</option>
                  <option value="자산관리 / WM (Wealth Management)부">자산관리 / WM (Wealth Management)부</option>
                  <option value="외환 / 무역금융부">외환 / 무역금융부</option>
                  <option value="투자은행부">투자은행부</option>
                  <option value="지속가능경영(ESG)부">지속가능경영(ESG)부</option>
                  <option value="인사부">인사부</option>
                  <option value="총무부">총무부</option>
                  <option value="CRM부">CRM부</option>
                </select>
              </div>

              {/* 팀 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  팀
                </label>
                <select
                  name="team_number"
                  value={formData.team_number}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  <option value="">선택하세요</option>
                  <option value="1팀">1팀</option>
                  <option value="2팀">2팀</option>
                  <option value="3팀">3팀</option>
                  <option value="4팀">4팀</option>
                  <option value="5팀">5팀</option>
                  <option value="6팀">6팀</option>
                  <option value="7팀">7팀</option>
                  <option value="8팀">8팀</option>
                  <option value="9팀">9팀</option>
                  <option value="10팀">10팀</option>
                </select>
              </div>

              {/* 관심사 */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  관심사 <span className="text-red-500">*</span> (3개 이상 선택)
                </label>
                
                {/* 관심사 선택 버튼 */}
                <button
                  type="button"
                  onClick={() => setShowInterests(!showInterests)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white text-gray-700 hover:border-primary-500 transition-colors"
                >
                  {formData.interests.length > 0 
                    ? `${formData.interests.length}개 선택됨` 
                    : '관심사를 선택하세요'
                  }
                </button>
                
                {/* 관심사 목록 (숨겨짐/보임) */}
                {showInterests && (
                  <div className="mt-3 p-4 border border-gray-300 rounded-lg bg-white">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {interestOptions.map((interest) => (
                        <button
                          key={interest}
                          type="button"
                          onClick={() => handleInterestToggle(interest)}
                          className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                            formData.interests.includes(interest)
                              ? 'bg-primary-600 text-white border-primary-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:border-primary-500'
                          } border`}
                        >
                          {interest}
                        </button>
                      ))}
                    </div>
                    <div className="mt-3 flex justify-between items-center">
                      <p className="text-sm text-gray-500">
                        선택된 관심사: {formData.interests.length}개
                      </p>
                      <button
                        type="button"
                        onClick={() => setShowInterests(false)}
                        className="px-3 py-1 text-sm bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
                      >
                        닫기
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '가입 중...' : '가입하기'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              이미 계정이 있으신가요?{' '}
              <Link to="/login" className="text-primary-600 font-semibold hover:text-primary-700">
                로그인
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

