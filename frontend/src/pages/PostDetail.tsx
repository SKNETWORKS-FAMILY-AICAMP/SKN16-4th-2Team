/**
 * 게시글 상세 페이지
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { postAPI } from '../utils/api'
import { 
  ArrowLeftIcon,
  ChatBubbleLeftIcon,
  EyeIcon,
  ClockIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'

export default function PostDetail() {
  const { postId } = useParams<{ postId: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<any>(null)
  const [comments, setComments] = useState<any[]>([])
  const [commentText, setCommentText] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [isAuthor, setIsAuthor] = useState(false)
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    if (postId) {
      loadPost()
    }
  }, [postId])

  const loadPost = async () => {
    try {
      setLoading(true)
      const data = await postAPI.getPost(Number(postId))
      console.log('Post data:', data) // 디버깅용 로그
      console.log('is_author:', data.is_author)
      console.log('is_admin:', data.is_admin)
      console.log('user role:', user?.role)
      setPost(data.post)
      setComments(data.comments || [])
      setIsAuthor(data.is_author || false)
      setIsAdmin(data.is_admin || false)
    } catch (error) {
      console.error('Failed to load post:', error)
      alert('게시글을 불러올 수 없습니다.')
      navigate('/board')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!commentText.trim() || submitting) return

    setSubmitting(true)
    try {
      await postAPI.createComment(Number(postId), commentText)
      setCommentText('')
      loadPost()
    } catch (error) {
      console.error('Failed to create comment:', error)
      alert('댓글 작성에 실패했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      e.stopPropagation()
      e.nativeEvent.stopImmediatePropagation()
      
      // 엔터키로 댓글 전송
      if (!submitting && commentText.trim()) {
        handleSubmitComment(e as any)
      }
      return false
    }
  }

  const handleDeletePost = async () => {
    if (!postId) return
    
    if (!window.confirm('정말로 이 글을 삭제하시겠습니까?')) {
      return
    }

    try {
      await postAPI.deletePost(Number(postId))
      alert('글이 삭제되었습니다.')
      navigate('/board')
    } catch (error) {
      console.error('Failed to delete post:', error)
      alert('글 삭제에 실패했습니다.')
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!window.confirm('정말로 이 댓글을 삭제하시겠습니까?')) {
      return
    }

    try {
      await postAPI.deleteComment(commentId)
      loadPost() // 댓글 목록 새로고침
    } catch (error) {
      console.error('Failed to delete comment:', error)
      alert('댓글 삭제에 실패했습니다.')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    )
  }

  if (!post) return null

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/board')}
        className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeftIcon className="w-5 h-5" />
        <span>목록으로</span>
      </button>

      {/* Post */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-md p-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-4">{post.title}</h1>
        
        <div className="flex items-center justify-between mb-6 pb-6 border-b">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span className="font-medium text-green-600">{post.author_alias}</span>
            <div className="flex items-center space-x-1">
              <ClockIcon className="w-4 h-4" />
              <span>{formatDate(post.created_at)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <EyeIcon className="w-4 h-4" />
              <span>{post.view_count}</span>
            </div>
            <div className="flex items-center space-x-1">
              <ChatBubbleLeftIcon className="w-4 h-4" />
              <span>{post.comment_count}</span>
            </div>
          </div>
          
          {/* 삭제 버튼 - 작성자 또는 관리자만 표시 */}
          {(() => {
            console.log('Delete button check - isAuthor:', isAuthor, 'isAdmin:', isAdmin, 'show:', (isAuthor || isAdmin))
            return (isAuthor || isAdmin) && (
              <button
                onClick={handleDeletePost}
                className="flex items-center space-x-1 px-3 py-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                title="글 삭제"
              >
                <TrashIcon className="w-4 h-4" />
                <span className="text-sm">삭제</span>
              </button>
            )
          })()}
        </div>

        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{post.content}</p>
        </div>
      </motion.div>

      {/* Comments */}
      <div className="bg-white rounded-xl shadow-md p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-6">
          댓글 {comments.length}
        </h2>

        {/* Comment List */}
        <div className="space-y-4 mb-6">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="p-4 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-green-600">{comment.author_alias}</span>
                  <span className="text-xs text-gray-500">{formatDate(comment.created_at)}</span>
                </div>
                
                {/* 댓글 삭제 버튼 - 작성자 또는 관리자만 표시 */}
                {(comment.is_author || comment.is_admin) && (
                  <button
                    onClick={() => handleDeleteComment(comment.id)}
                    className="flex items-center space-x-1 px-2 py-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                    title="댓글 삭제"
                  >
                    <TrashIcon className="w-3 h-3" />
                    <span className="text-xs">삭제</span>
                  </button>
                )}
              </div>
              <p className="text-gray-700 whitespace-pre-wrap">{comment.content}</p>
            </div>
          ))}
          {comments.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              첫 댓글을 작성해보세요!
            </p>
          )}
        </div>

        {/* Comment Form */}
        <form onSubmit={handleSubmitComment} className="space-y-4">
          <textarea
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="댓글을 입력하세요... (엔터로 전송, Shift+엔터로 줄바꿈)"
            rows={4}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting || !commentText.trim()}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '작성 중...' : '댓글 작성'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}



