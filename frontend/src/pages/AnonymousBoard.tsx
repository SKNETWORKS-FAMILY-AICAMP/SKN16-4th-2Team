/**
 * 익명 게시판 (대나무숲) 페이지
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { postAPI } from '../utils/api'
import { 
  PlusIcon, 
  ChatBubbleLeftIcon,
  EyeIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'

export default function AnonymousBoard() {
  const [posts, setPosts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)

  useEffect(() => {
    loadPosts()
  }, [])

  const loadPosts = async () => {
    try {
      setLoading(true)
      setError(null)
      console.log('Loading posts...')
      const data = await postAPI.getPosts()
      console.log('Posts loaded successfully:', data)
      setPosts(data)
    } catch (error) {
      console.error('Failed to load posts:', error)
      console.error('Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      })
      setError(`게시글을 불러올 수 없습니다. (${error.response?.status || 'Unknown'}) 로그인 상태를 확인해주세요.`)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (minutes < 1) return '방금 전'
    if (minutes < 60) return `${minutes}분 전`
    if (hours < 24) return `${hours}시간 전`
    if (days < 7) return `${days}일 전`
    return date.toLocaleDateString('ko-KR')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">대나무숲 🎋</h1>
          <p className="text-gray-600 mt-1">익명으로 자유롭게 소통하세요</p>
        </div>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          <span>글쓰기</span>
        </button>
      </div>

      {/* Notice */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-4">
        <p className="text-green-900 text-sm">
          ✨ 이곳은 완전 익명이 보장되는 공간입니다. 서로를 존중하며 건전한 소통 문화를 만들어주세요.
        </p>
      </div>

      {/* Posts List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : error ? (
        <div className="text-center py-12 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadPosts}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            다시 시도
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} formatDate={formatDate} />
          ))}
          {posts.length === 0 && (
            <div className="text-center py-12 bg-white rounded-xl">
              <p className="text-gray-600">아직 게시글이 없습니다. 첫 글을 작성해보세요!</p>
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {createModalOpen && (
        <CreatePostModal
          onClose={() => setCreateModalOpen(false)}
          onSuccess={() => {
            setCreateModalOpen(false)
            loadPosts()
          }}
        />
      )}
    </div>
  )
}

function PostCard({ post, formatDate }: any) {
  return (
    <Link to={`/board/${post.id}`}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: 1.01 }}
        className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-all cursor-pointer"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{post.title}</h3>
        <p className="text-gray-600 mb-4 line-clamp-2">{post.content}</p>
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <ClockIcon className="w-4 h-4" />
              <span>{formatDate(post.created_at)}</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <EyeIcon className="w-4 h-4" />
              <span>{post.view_count}</span>
            </div>
            <div className="flex items-center space-x-1">
              <ChatBubbleLeftIcon className="w-4 h-4" />
              <span>{post.comment_count}</span>
            </div>
          </div>
        </div>
      </motion.div>
    </Link>
  )
}

function CreatePostModal({ onClose, onSuccess }: any) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !content.trim()) return

    setLoading(true)
    try {
      await postAPI.createPost(title, content)
      onSuccess()
    } catch (error) {
      console.error('Failed to create post:', error)
      alert('글 작성에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl p-8 max-w-2xl w-full"
      >
        <h2 className="text-2xl font-bold text-gray-900 mb-6">글쓰기 (익명)</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="제목을 입력하세요"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-lg font-medium"
            />
          </div>
          <div>
            <textarea
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="내용을 입력하세요"
              rows={10}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
            />
          </div>
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 font-medium"
            >
              {loading ? '작성 중...' : '작성하기'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}



