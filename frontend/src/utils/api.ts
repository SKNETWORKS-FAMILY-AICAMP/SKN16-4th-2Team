/**
 * API 클라이언트
 * Axios 기반 HTTP 요청 처리
 */
import axios, { AxiosError } from 'axios'
import { useAuthStore } from '../store/authStore'

// Docker 환경에서는 Vite의 proxy를 통해 /api로 접근
// 로컬 개발 환경에서는 http://localhost:8000 사용
const API_URL = import.meta.env.VITE_API_URL || '/api'

// Axios 인스턴스 생성
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 요청 인터셉터: 토큰 자동 추가
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터: 에러 처리
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error)
    
    if (error.response?.status === 401) {
      // 토큰 만료 시 로그아웃
      useAuthStore.getState().logout()
      window.location.href = '/login'
    } else if (error.code === 'ECONNREFUSED' || error.code === 'NETWORK_ERROR') {
      // 네트워크 에러 처리
      console.error('Network error - server may be down')
    }
    
    return Promise.reject(error)
  }
)

// API 함수들

// 인증
export const authAPI = {
  login: async (email: string, password: string) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  register: async (userData: any) => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
  
  updateProfile: async (userData: any) => {
    const response = await api.put('/auth/me', userData)
    return response.data
  },
  
  findId: async (name: string, employeeNumber: string) => {
    const response = await api.post('/auth/find-id', null, {
      params: { name, employee_number: employeeNumber }
    })
    return response.data
  },
  
  resetPassword: async (email: string, employeeNumber: string, newPassword: string) => {
    const response = await api.post('/auth/reset-password', null, {
      params: { 
        email, 
        employee_number: employeeNumber,
        new_password: newPassword
      }
    })
    return response.data
  },
}

// 챗봇
export const chatAPI = {
  sendMessage: async (message: string) => {
    const response = await api.post('/chat/', { message })
    return response.data
  },
  
  getHistory: async (limit: number = 10) => {
    const response = await api.get(`/chat/history?limit=${limit}`)
    return response.data
  },
  
  provideFeedback: async (chatId: number, isHelpful: boolean) => {
    const response = await api.post(`/chat/feedback/${chatId}`, { is_helpful: isHelpful })
    return response.data
  },
}

// 문서
export const documentAPI = {
  getDocuments: async (category?: string) => {
    const params = category ? `?category=${encodeURIComponent(category)}` : ''
    const response = await api.get(`/documents/${params}`)
    return response.data
  },
  
  getDocument: async (id: number) => {
    const response = await api.get(`/documents/${id}`)
    return response.data
  },
  
  uploadDocument: async (file: File, title: string, category: string, description?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    formData.append('category', category)
    if (description) formData.append('description', description)
    
    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  
  downloadDocument: async (id: number) => {
    const response = await api.get(`/documents/${id}/download`, {
      responseType: 'blob',
    })
    return response.data
  },
  
  deleteDocument: async (id: number) => {
    const response = await api.delete(`/documents/${id}`)
    return response.data
  },
  
  getCategories: async () => {
    const response = await api.get('/documents/categories/list')
    return response.data
  },
}

// 게시판
export const postAPI = {
  getPosts: async (skip: number = 0, limit: number = 20) => {
    const response = await api.get(`/posts/?skip=${skip}&limit=${limit}`)
    return response.data
  },
  
  getPost: async (id: number) => {
    const response = await api.get(`/posts/${id}`)
    return response.data
  },
  
  createPost: async (title: string, content: string) => {
    const response = await api.post('/posts/', { title, content })
    return response.data
  },
  
  deletePost: async (id: number) => {
    const response = await api.delete(`/posts/${id}`)
    return response.data
  },
  
  createComment: async (postId: number, content: string) => {
    const response = await api.post('/posts/comments', { post_id: postId, content })
    return response.data
  },
  
  deleteComment: async (id: number) => {
    const response = await api.delete(`/posts/comments/${id}`)
    return response.data
  },
}

// 대시보드
export const dashboardAPI = {
  getMenteeDashboard: async () => {
    const response = await api.get('/dashboard/mentee')
    return response.data
  },
  
  getMentorDashboard: async () => {
    const response = await api.get('/dashboard/mentor')
    return response.data
  },
  
  assignMentor: async (menteeId: number, mentorId: number) => {
    const response = await api.post('/dashboard/assign-mentor', { mentee_id: menteeId, mentor_id: mentorId })
    return response.data
  },
  
  addExamScore: async (menteeId: number, examName: string, scoreData: any, totalScore: number, grade?: string) => {
    const response = await api.post('/dashboard/exam-score', {
      mentee_id: menteeId,
      exam_name: examName,
      score_data: scoreData,
      total_score: totalScore,
      grade,
    })
    return response.data
  },
}

export default api

