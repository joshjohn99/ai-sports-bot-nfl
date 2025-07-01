import { useState, useEffect } from 'react'
import { SportsCarousel } from '../src/sports_bot/components/carousel/SportsCarousel'
import DebateArena from '../components/DebateArena'

export default function Home() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '🏈 Ready to analyze any sports debate! I have access to live data from 2,920+ NFL players and 407+ NBA players.',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('checking')

  // Test backend connection
  useEffect(() => {
    testConnection()
  }, [])

  const testConnection = async () => {
    try {
      setConnectionStatus('checking')
      const response = await fetch('/api/sports/leaders?sport=NFL&metric=yards&limit=4')
      if (response.ok) {
        setConnectionStatus('connected')
      } else {
        setConnectionStatus('error')
      }
    } catch (error) {
      setConnectionStatus('error')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/start-debate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'demo_user',
          topic: input.trim()
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        // Add each response as a separate message
        data.responses?.forEach((resp, index) => {
          const assistantMessage = {
            id: Date.now() + index,
            type: 'assistant',
            content: resp.content || resp.message || 'Processing your debate...',
            timestamp: new Date(),
            data: resp
          }
          
          setTimeout(() => {
            setMessages(prev => [...prev, assistantMessage])
          }, index * 500) // Stagger responses
        })
      } else {
        throw new Error(`Backend error: ${response.status}`)
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now(),
        type: 'system',
        content: `⚠️ Error: ${error.message}. Please check that the backend is running and try again.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const ConnectionIndicator = () => (
    <div className="flex items-center gap-2 mb-4">
      <div className={`w-3 h-3 rounded-full ${
        connectionStatus === 'connected' ? 'bg-green-400 animate-pulse' :
        connectionStatus === 'checking' ? 'bg-yellow-400 animate-pulse' :
        'bg-red-400'
      }`} />
      <span className="text-sm font-medium text-slate-300">
        {connectionStatus === 'connected' ? 'Active Debate' :
         connectionStatus === 'checking' ? 'Connecting...' :
         'Backend error: 500'}
      </span>
      {connectionStatus === 'connected' && (
        <span className="text-xs text-slate-500">Ready to start</span>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header - OpenAI Operator Style */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-lg">🏆</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                  AI Sports Bot Dashboard
                </h1>
                <p className="text-sm text-slate-400">Real-time sports data with intelligent multi-bot debates</p>
              </div>
            </div>
            <ConnectionIndicator />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Debate Arena */}
        <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 rounded-2xl border border-slate-800 p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-xl">🏟️</span>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">AI Sports Debate Arena</h2>
                <p className="text-sm text-slate-400">Real data • Multi-bot debates • {messages.length > 1 ? `${messages.length - 1} interactions` : 'Ready to start'}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-slate-400">2,920+ NFL players</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-slate-400">407+ NBA players</span>
              </div>
            </div>
          </div>

          {/* Debate Participants */}
          <div className="flex items-center gap-4 mb-6 p-4 bg-slate-800/30 rounded-xl">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">👤</div>
              <span className="text-sm font-medium text-slate-300">You</span>
            </div>
            <div className="w-6 h-px bg-slate-600"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">📊</div>
              <span className="text-sm font-medium text-blue-300">Stats Expert</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">❤️</div>
              <span className="text-sm font-medium text-purple-300">Analysis Bot</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">⚖️</div>
              <span className="text-sm font-medium text-green-300">Debate Judge</span>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="h-96 overflow-y-auto space-y-4 mb-6 p-4 bg-slate-900/30 rounded-xl border border-slate-700">
            {messages.map((message) => (
              <div key={message.id} className={`flex gap-3 ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}>
                <div className={`max-w-2xl p-4 rounded-2xl ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white ml-auto' 
                    : message.type === 'system'
                    ? 'bg-red-900/30 border border-red-800 text-red-200'
                    : 'bg-slate-800 text-slate-100 border border-slate-700'
                }`}>
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </div>
                  <div className="text-xs opacity-60 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="bg-slate-800 border border-slate-700 p-4 rounded-2xl">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-75"></div>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse delay-150"></div>
                    <span className="text-sm text-slate-400 ml-2">Analyzing your question...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask any sports question... (e.g., 'Who's better: Mahomes or Josh Allen?')"
              className="flex-1 px-4 py-3 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isLoading ? 'Processing...' : 'Start Debate'}
            </button>
          </form>
        </div>

        {/* Sports Data Display */}
        <SportsCarousel />
      </div>
    </div>
  )
} 