/**
 * 플로팅 챗봇 컴포넌트
 * RAG 기반 AI 챗봇
 */
import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { 
  ChatBubbleLeftRightIcon, 
  XMarkIcon, 
  PaperAirplaneIcon,
  SparklesIcon
} from '@heroicons/react/24/solid'
import { chatAPI } from '../utils/api'

interface Message {
  id: string
  text: string
  isBot: boolean
  sources?: any[]
  timestamp: Date
}

interface ChatBotProps {
  forceOpen?: boolean
  onClose?: () => void
}

export default function ChatBot({ forceOpen = false, onClose }: ChatBotProps = {}) {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '안녕하세요! 저는 AI 하리보예요 🐻\n하경은행 온보딩 플랫폼에서 무엇이든 도와드릴게요!\n궁금한 점을 자유롭게 물어보세요.',
      isBot: true,
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (forceOpen) {
      setIsOpen(true)
    }
  }, [forceOpen])

  const handleClose = () => {
    setIsOpen(false)
    if (onClose) {
      onClose()
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      isBot: false,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatAPI.sendMessage(input)
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        isBot: true,
        sources: response.sources,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '앗, 잠깐만요! 🐻\n일시적인 오류가 발생했어요.\n잠시 후 다시 시도해주세요.',
        isBot: true,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSourceClick = (sourceTitle: string) => {
    // "RAG - " 접두사 제거
    const cleanTitle = sourceTitle.replace('RAG - ', '')
    // 자료실로 이동하면서 검색어를 URL 파라미터로 전달
    navigate(`/documents?search=${encodeURIComponent(cleanTitle)}`)
  }

  return (
    <>
      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-24 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col z-40"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-primary-600 via-primary-500 to-amber-500 p-4 rounded-t-2xl flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <img src="/assets/bear.png" alt="하경곰" className="w-10 h-10 rounded-full shadow-md" />
                <div>
                  <h3 className="font-bold text-white">AI 하리보</h3>
                  <p className="text-xs text-white/90">온보딩 파트너 🐻</p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="text-white hover:bg-white/20 p-2 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.isBot
                        ? 'bg-gradient-to-r from-primary-50 to-amber-50 text-bank-800 border border-primary-200'
                        : 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-300">
                        <p className="text-xs text-gray-600 mb-1">참고 자료:</p>
                        {(() => {
                          // 중복 제거 (title 기준)
                          const uniqueSources = message.sources.filter((source, index, self) => 
                            index === self.findIndex(s => s.title === source.title)
                          );
                          return uniqueSources.slice(0, 3).map((source, idx) => (
                            <p 
                              key={idx} 
                              className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer hover:underline"
                              onClick={() => handleSourceClick(source.title)}
                            >
                              • {source.title.replace('RAG - ', '')}
                            </p>
                          ));
                        })()}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gradient-to-r from-primary-50 to-amber-50 rounded-2xl px-4 py-3 border border-primary-200">
                    <div className="flex items-center space-x-2">
                      <img src="/assets/bear.png" alt="하경곰" className="w-4 h-4 rounded-full" />
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce delay-100"></div>
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce delay-200"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-primary-100">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="AI 하리보에게 질문해보세요..."
                  className="flex-1 px-4 py-3 border border-primary-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white/50 backdrop-blur-sm"
                  disabled={loading}
                />
                <button
                  onClick={handleSend}
                  disabled={loading || !input.trim()}
                  className="p-3 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl hover:from-primary-700 hover:to-primary-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
                >
                  <PaperAirplaneIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Button */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => {
          if (isOpen) {
            handleClose()
          } else {
            setIsOpen(true)
          }
        }}
        className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 text-white rounded-full shadow-lg flex items-center justify-center z-50 hover:shadow-xl transition-shadow"
      >
        {isOpen ? (
          <XMarkIcon className="w-8 h-8" />
        ) : (
          <div className="relative">
            <img src="/assets/bear.png" alt="하경곰" className="w-10 h-10 rounded-full" />
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-accent-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">💬</span>
            </div>
          </div>
        )}
      </motion.button>
    </>
  )
}



