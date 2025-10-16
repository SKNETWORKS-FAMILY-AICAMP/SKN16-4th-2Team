/**
 * 자료실 페이지
 */
import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { documentAPI } from '../utils/api'
import { 
  DocumentTextIcon, 
  ArrowDownTrayIcon, 
  PlusIcon,
  MagnifyingGlassIcon,
  FolderIcon
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'

export default function Documents() {
  const { user } = useAuthStore()
  const [documents, setDocuments] = useState<any[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [uploadModalOpen, setUploadModalOpen] = useState(false)

  useEffect(() => {
    loadDocuments()
    loadCategories()
  }, [selectedCategory])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const data = await documentAPI.getDocuments(selectedCategory || undefined)
      setDocuments(data)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const data = await documentAPI.getCategories()
      setCategories(data.categories)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const handleDownload = async (id: number, title: string) => {
    try {
      const blob = await documentAPI.downloadDocument(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = title
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      alert('다운로드에 실패했습니다.')
    }
  }

  const filteredDocuments = documents.filter((doc) =>
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">자료실</h1>
          <p className="text-gray-600 mt-1">업무에 필요한 모든 자료를 찾아보세요</p>
        </div>
        {user?.role === 'admin' && (
          <button
            onClick={() => setUploadModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            <span>문서 업로드</span>
          </button>
        )}
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <div className="grid md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="문서 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="">전체 카테고리</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FolderIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">문서가 없습니다</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredDocuments.map((doc) => (
                <DocumentListItem
                  key={doc.id}
                  document={doc}
                  onDownload={handleDownload}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Upload Modal */}
      {uploadModalOpen && (
        <UploadModal
          categories={categories}
          onClose={() => setUploadModalOpen(false)}
          onSuccess={() => {
            setUploadModalOpen(false)
            loadDocuments()
          }}
        />
      )}
    </div>
  )
}

function DocumentListItem({ document, onDownload }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="p-6 hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-center space-x-4">
        {/* 문서 아이콘 */}
        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <DocumentTextIcon className="w-5 h-5 text-primary-600" />
        </div>
        
        {/* 문서 정보 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-4">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate">{document.title}</h3>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                  <span>{document.category}</span>
                </span>
                <span>{document.file_type}</span>
                <span>다운로드: {document.download_count}</span>
              </div>
              {document.description && (
                <p className="text-sm text-gray-500 mt-1 truncate">{document.description}</p>
              )}
            </div>
            
            {/* 다운로드 버튼 */}
            <button
              onClick={() => onDownload(document.id, document.title + document.file_type)}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex-shrink-0"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              <span>다운로드</span>
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function UploadModal({ categories, onClose, onSuccess }: any) {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [category, setCategory] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !title || !category) return

    setLoading(true)
    try {
      await documentAPI.uploadDocument(file, title, category, description)
      onSuccess()
    } catch (error) {
      console.error('Upload failed:', error)
      alert('업로드에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl p-8 max-w-md w-full"
      >
        <h2 className="text-2xl font-bold text-gray-900 mb-6">문서 업로드</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">제목 *</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">카테고리 *</label>
            <select
              required
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">선택하세요</option>
              {categories.map((cat: string) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">설명</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">파일 *</label>
            <input
              type="file"
              required
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              accept=".pdf,.txt,.docx,.doc,.xlsx,.xls,.pptx,.ppt"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
            >
              {loading ? '업로드 중...' : '업로드'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}



