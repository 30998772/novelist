import { useState, useRef, useEffect } from 'react'
import { streamChat, fetchSessions, fetchHistory, deleteSession } from '../api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  onRefresh: () => void
}

export default function ChatPanel({ onRefresh }: Props) {
  const [sessions, setSessions] = useState<string[]>([])
  const [currentSession, setCurrentSession] = useState('default')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 加载 session 列表
  useEffect(() => {
    fetchSessions().then(setSessions)
  }, [])

  // 切换 session 时加载历史
  useEffect(() => {
    fetchHistory(currentSession).then(setMessages)
  }, [currentSession])

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || loading) return

    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    let assistantContent = ''

    streamChat(
      userMsg,
      currentSession,
      (chunk) => {
        assistantContent += chunk
        setMessages(prev => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last?.role === 'assistant') {
            last.content = assistantContent
          } else {
            updated.push({ role: 'assistant', content: assistantContent })
          }
          return updated
        })
      },
      () => {
        setLoading(false)
        onRefresh()
        fetchSessions().then(setSessions)
      },
      (err) => {
        setLoading(false)
        setMessages(prev => [...prev, { role: 'assistant', content: `[错误: ${err}]` }])
      },
    )
  }

  const handleNewSession = () => {
    const id = `session_${Date.now()}`
    setCurrentSession(id)
    setMessages([])
    fetchSessions().then(setSessions)
  }

  const handleDeleteSession = async (id: string) => {
    await deleteSession(id)
    if (currentSession === id) {
      setCurrentSession('default')
    }
    fetchSessions().then(setSessions)
  }

  return (
    <div className="flex flex-col h-full">
      {/* 顶栏 */}
      <div className="p-3 border-b border-gray-700 flex items-center gap-2">
        <select
          value={currentSession}
          onChange={e => setCurrentSession(e.target.value)}
          className="bg-gray-800 text-white px-3 py-1.5 rounded text-sm flex-1"
        >
          {sessions.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button
          onClick={handleNewSession}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm"
        >
          新建
        </button>
        <button
          onClick={() => handleDeleteSession(currentSession)}
          className="px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded text-sm"
        >
          删除
        </button>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-100'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="p-3 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="输入消息..."
            disabled={loading}
            className="flex-1 bg-gray-800 text-white px-4 py-2 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 rounded text-sm"
          >
            {loading ? '思考中...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  )
}
