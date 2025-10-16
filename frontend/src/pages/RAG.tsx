/**
 * RAG 문서 업로드 페이지
 * 다중 TXT 파일 업로드 및 RAG 시스템 인덱싱
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  CloudArrowUpIcon, 
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import api from '../utils/api'

interface UploadedFile {
  id: number
  title: string
  file_size: number
  upload_date: string
  is_indexed: boolean
}

export default function RAG() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadedDocs, setUploadedDocs] = useState<UploadedFile[]>([])
  const [uploadStatus, setUploadStatus] = useState<{type: 'success' | 'error', message: string} | null>(null)
  const [deletingDoc, setDeletingDoc] = useState<number | null>(null)
  
  // 체크박스 선택 관련 상태
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([])
  const [isAllSelected, setIsAllSelected] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deletingMultiple, setDeletingMultiple] = useState(false)

  // 페이지 로드 시 기존 문서 목록 불러오기
  useEffect(() => {
    loadExistingDocuments()
    loadLocalDocuments()
  }, [])

  // 로컬 스토리지에서 문서 목록 불러오기
  const loadLocalDocuments = () => {
    try {
      const savedDocs = localStorage.getItem('rag-uploaded-docs')
      if (savedDocs) {
        const docs = JSON.parse(savedDocs)
        setUploadedDocs(docs)
      }
    } catch (error) {
      console.error('Failed to load local documents:', error)
    }
  }

  // 로컬 스토리지에 문서 목록 저장
  const saveLocalDocuments = (docs: UploadedFile[]) => {
    try {
      localStorage.setItem('rag-uploaded-docs', JSON.stringify(docs))
    } catch (error) {
      console.error('Failed to save local documents:', error)
    }
  }

  const loadExistingDocuments = async () => {
    try {
      const response = await api.get('/documents/?category=RAG')
      // 서버에서 가져온 데이터와 로컬 데이터 병합
      const serverDocs = response.data
      const localDocs = JSON.parse(localStorage.getItem('rag-uploaded-docs') || '[]')
      
      // 서버 데이터를 우선하고, 로컬에만 있는 데이터는 유지
      const mergedDocs = [...serverDocs]
      localDocs.forEach((localDoc: UploadedFile) => {
        if (!serverDocs.find((serverDoc: UploadedFile) => serverDoc.id === localDoc.id)) {
          mergedDocs.push(localDoc)
        }
      })
      
      setUploadedDocs(mergedDocs)
      saveLocalDocuments(mergedDocs)
    } catch (error) {
      console.error('Failed to load documents:', error)
      // 서버 오류 시 로컬 데이터만 로드
      loadLocalDocuments()
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      const txtFiles = files.filter(file => file.name.endsWith('.txt'))
      
      if (txtFiles.length !== files.length) {
        setUploadStatus({
          type: 'error',
          message: 'TXT 파일만 업로드 가능합니다.'
        })
        setTimeout(() => setUploadStatus(null), 3000)
      }
      
      setSelectedFiles(prev => [...prev, ...txtFiles])
    }
  }

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setUploadStatus({
        type: 'error',
        message: '업로드할 파일을 선택해주세요.'
      })
      setTimeout(() => setUploadStatus(null), 3000)
      return
    }

    setUploading(true)
    setUploadStatus(null)

    try {
      const formData = new FormData()
      selectedFiles.forEach(file => {
        formData.append('files', file)
      })

      const response = await api.post('/documents/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const newDocs = [...response.data, ...uploadedDocs]
      setUploadedDocs(newDocs)
      saveLocalDocuments(newDocs)
      setSelectedFiles([])
      setUploadStatus({
        type: 'success',
        message: `${response.data.length}개의 파일이 성공적으로 업로드되고 인덱싱되었습니다!`
      })
      setTimeout(() => setUploadStatus(null), 5000)

    } catch (error: any) {
      console.error('Upload error:', error)
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || '업로드 중 오류가 발생했습니다.'
      })
      setTimeout(() => setUploadStatus(null), 5000)
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm('정말로 이 문서를 삭제하시겠습니까?\n\n⚠️ 영구적으로 삭제됩니다. 복구할 수 없습니다.')) {
      return
    }

    setDeletingDoc(docId)
    try {
      await api.delete(`/documents/${docId}`)
      const updatedDocs = uploadedDocs.filter(doc => doc.id !== docId)
      setUploadedDocs(updatedDocs)
      saveLocalDocuments(updatedDocs)
      setUploadStatus({
        type: 'success',
        message: '문서가 성공적으로 삭제되었습니다.'
      })
      setTimeout(() => setUploadStatus(null), 3000)
    } catch (error: any) {
      console.error('Delete error:', error)
      // 서버 삭제 실패해도 로컬에서는 제거
      const updatedDocs = uploadedDocs.filter(doc => doc.id !== docId)
      setUploadedDocs(updatedDocs)
      saveLocalDocuments(updatedDocs)
      setUploadStatus({
        type: 'error',
        message: '서버에서 삭제는 실패했지만 로컬에서 제거되었습니다.'
      })
      setTimeout(() => setUploadStatus(null), 5000)
    } finally {
      setDeletingDoc(null)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  // 체크박스 관련 함수들
  const handleSelectDoc = (docId: number) => {
    setSelectedDocIds(prev => {
      const newSelected = prev.includes(docId) 
        ? prev.filter(id => id !== docId)
        : [...prev, docId]
      
      // 전체 선택 상태 업데이트
      setIsAllSelected(newSelected.length === uploadedDocs.length)
      return newSelected
    })
  }

  const handleSelectAll = () => {
    if (isAllSelected) {
      setSelectedDocIds([])
      setIsAllSelected(false)
    } else {
      setSelectedDocIds(uploadedDocs.map(doc => doc.id))
      setIsAllSelected(true)
    }
  }

  const handleDeleteSelected = () => {
    if (selectedDocIds.length === 0) return
    setShowDeleteModal(true)
  }

  const confirmDeleteSelected = async () => {
    setDeletingMultiple(true)
    setShowDeleteModal(false)
    
    try {
      // 선택된 문서들을 하나씩 삭제
      for (const docId of selectedDocIds) {
        await api.delete(`/documents/${docId}`)
      }
      
      // 로컬 상태 업데이트
      const updatedDocs = uploadedDocs.filter(doc => !selectedDocIds.includes(doc.id))
      setUploadedDocs(updatedDocs)
      saveLocalDocuments(updatedDocs)
      
      // 선택 상태 초기화
      setSelectedDocIds([])
      setIsAllSelected(false)
      
      setUploadStatus({
        type: 'success',
        message: `${selectedDocIds.length}개의 문서가 성공적으로 삭제되었습니다.`
      })
      setTimeout(() => setUploadStatus(null), 5000)
      
    } catch (error: any) {
      console.error('Bulk delete error:', error)
      setUploadStatus({
        type: 'error',
        message: '일부 문서 삭제에 실패했습니다.'
      })
      setTimeout(() => setUploadStatus(null), 5000)
    } finally {
      setDeletingMultiple(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">RAG 문서 업로드</h1>
        <p className="text-purple-100">
          TXT 파일을 업로드하면 챗봇이 해당 문서를 기반으로 답변합니다
        </p>
      </div>

      {/* Status Message */}
      {uploadStatus && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-lg flex items-center space-x-2 ${
            uploadStatus.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircleIcon className="w-5 h-5" />
          ) : (
            <XCircleIcon className="w-5 h-5" />
          )}
          <span>{uploadStatus.message}</span>
        </motion.div>
      )}

      {/* Upload Area */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="space-y-6">
          {/* File Input */}
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-purple-400 transition-colors">
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".txt"
              onChange={handleFileSelect}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <CloudArrowUpIcon className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                TXT 파일을 선택하거나 드래그하세요
              </p>
              <p className="text-sm text-gray-500">
                여러 파일을 한 번에 선택할 수 있습니다
              </p>
            </label>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-900">선택된 파일 ({selectedFiles.length})</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center space-x-3">
                      <DocumentTextIcon className="w-5 h-5 text-purple-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1 hover:bg-gray-200 rounded transition-colors"
                    >
                      <TrashIcon className="w-5 h-5 text-red-600" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full mt-4 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    업로드 중...
                  </span>
                ) : (
                  `${selectedFiles.length}개 파일 업로드`
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Uploaded Documents */}
      {uploadedDocs.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">
              업로드된 문서 ({uploadedDocs.length})
            </h2>
            
            {/* 일괄 작업 버튼들 */}
            <div className="flex items-center space-x-3">
              <button
                onClick={handleSelectAll}
                className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <CheckIcon className="w-4 h-4" />
                <span>{isAllSelected ? '전체 해제' : '전체 선택'}</span>
              </button>
              
              {selectedDocIds.length > 0 && (
                <button
                  onClick={handleDeleteSelected}
                  disabled={deletingMultiple}
                  className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <TrashIcon className="w-4 h-4" />
                  <span>선택 삭제 ({selectedDocIds.length})</span>
                </button>
              )}
            </div>
          </div>
          
          <div className="space-y-2">
            {uploadedDocs.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                  selectedDocIds.includes(doc.id)
                    ? 'bg-purple-50 border-purple-200'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center space-x-3">
                  {/* 체크박스 */}
                  <input
                    type="checkbox"
                    checked={selectedDocIds.includes(doc.id)}
                    onChange={() => handleSelectDoc(doc.id)}
                    className="w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
                  />
                  
                  <DocumentTextIcon className="w-6 h-6 text-purple-600" />
                  <div>
                    <p className="font-medium text-gray-900">{doc.title}</p>
                    <p className="text-sm text-gray-500">
                      {formatFileSize(doc.file_size)} • {new Date(doc.upload_date).toLocaleDateString('ko-KR')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  {doc.is_indexed && (
                    <div className="flex items-center space-x-2 text-green-600">
                      <CheckCircleIcon className="w-5 h-5" />
                      <span className="text-sm font-medium">인덱싱 완료</span>
                    </div>
                  )}
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    disabled={deletingDoc === doc.id}
                    className="p-2 hover:bg-red-100 rounded-lg transition-colors text-red-600 disabled:opacity-50"
                    title="문서 삭제"
                  >
                    {deletingDoc === doc.id ? (
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <TrashIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-blue-900 mb-2">💡 사용 방법</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>• TXT 파일만 업로드 가능합니다</li>
          <li>• 여러 파일을 한 번에 선택하여 업로드할 수 있습니다</li>
          <li>• 업로드된 문서는 자동으로 RAG 시스템에 인덱싱됩니다</li>
          <li>• 챗봇에서 질문하면 업로드된 문서를 기반으로 답변합니다</li>
          <li>• 우측 하단의 챗봇 아이콘을 클릭하여 대화를 시작하세요</li>
        </ul>
      </div>

      {/* 삭제 확인 모달 */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl p-6 max-w-md w-full mx-4"
          >
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">문서 삭제 확인</h3>
                <p className="text-sm text-gray-500">이 작업은 되돌릴 수 없습니다</p>
              </div>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-700 mb-2">
                정말로 <span className="font-semibold text-red-600">{selectedDocIds.length}개의 문서</span>를 삭제하시겠습니까?
              </p>
              <p className="text-sm text-red-600 font-medium">
                ⚠️ 영구적으로 삭제됩니다. 복구할 수 없습니다.
              </p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                취소
              </button>
              <button
                onClick={confirmDeleteSelected}
                disabled={deletingMultiple}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deletingMultiple ? '삭제 중...' : '삭제하기'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

