import { useState, useRef, useEffect } from 'react'
import { Send, Users, Brain, BarChart3, Scale, Loader2 } from 'lucide-react'

export default function DebateArena() {
  const [messages, setMessages] = useState([
    {
      id: 0,
      sender: "⚖️ Debate Judge",
      content: "🏟️ **Welcome to the AI Sports Debate Arena!**\n\nAsk any sports question and watch our expert bots debate with **real data** from 2,920+ NFL players and 407+ NBA players.\n\n**Example questions:**\n• Who's the better QB: Mahomes or Allen?\n• Should the Lakers trade for a center?\n• Which team has the best defense?\n• Compare rookie performances this season\n\n*What would you like to debate?*",
      timestamp: new Date().toLocaleTimeString(),
      data_points: []
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [debateId, setDebateId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: messages.length,
      sender: "You",
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString(),
      data_points: []
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      console.log('🏟️ Starting debate for:', input.trim())
      
      const response = await fetch('/api/start-debate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: input.trim(),
          user_id: "frontend_user"
        })
      })

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`)
      }

      const data = await response.json()
      console.log('✅ Debate response:', data)

      if (data.success && data.messages) {
        setDebateId(data.debate_id)
        
        // Add bot messages with delay for realistic effect
        for (let i = 0; i < data.messages.length; i++) {
          await new Promise(resolve => setTimeout(resolve, 1500)) // 1.5s delay between bots
          
          const botMessage = {
            ...data.messages[i],
            id: messages.length + i + 1,
            timestamp: new Date().toLocaleTimeString()
          }
          
          setMessages(prev => [...prev, botMessage])
        }
      } else {
        throw new Error(data.error || 'Unknown debate error')
      }

    } catch (error) {
      console.error('❌ Debate error:', error)
      
      const errorMessage = {
        id: messages.length + 1,
        sender: "⚠️ System",
        content: `**Error starting debate:** ${error.message}\n\nPlease check that the backend is running and try again.`,
        timestamp: new Date().toLocaleTimeString(),
        data_points: []
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const getBotIcon = (sender) => {
    if (sender.includes('Stats Expert')) return <BarChart3 className="w-5 h-5" />
    if (sender.includes('Analysis Bot')) return <Brain className="w-5 h-5" />
    if (sender.includes('Judge')) return <Scale className="w-5 h-5" />
    if (sender === 'You') return <Users className="w-5 h-5" />
    return <Brain className="w-5 h-5" />
  }

  const getBotColor = (sender) => {
    if (sender.includes('Stats Expert')) return 'border-l-blue-500 bg-blue-50'
    if (sender.includes('Analysis Bot')) return 'border-l-purple-500 bg-purple-50'
    if (sender.includes('Judge')) return 'border-l-green-500 bg-green-50'
    if (sender === 'You') return 'border-l-gray-500 bg-gray-50'
    return 'border-l-gray-400 bg-gray-50'
  }

  return (
    <div className="max-w-6xl mx-auto bg-white rounded-lg shadow-lg border">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">🏟️ AI Sports Debate Arena</h1>
            <p className="text-blue-100">Real data • Multi-bot debates • 2,920+ NFL players • 407+ NBA players</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-blue-100">Active Debate</div>
            <div className="font-semibold">{debateId || 'Ready to start'}</div>
          </div>
        </div>
      </div>

      {/* Participants */}
      <div className="bg-gray-50 border-b p-4">
        <div className="flex items-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-gray-600" />
            <span className="font-medium">You</span>
          </div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <span className="font-medium">📊 Stats Expert</span>
          </div>
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-purple-600" />
            <span className="font-medium">🧠 Analysis Bot</span>
          </div>
          <div className="flex items-center space-x-2">
            <Scale className="w-4 h-4 text-green-600" />
            <span className="font-medium">⚖️ Debate Judge</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="h-96 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`border-l-4 p-4 rounded-r-lg ${getBotColor(message.sender)}`}
          >
            <div className="flex items-center space-x-2 mb-2">
              {getBotIcon(message.sender)}
              <span className="font-semibold text-gray-800">{message.sender}</span>
              <span className="text-xs text-gray-500">{message.timestamp}</span>
            </div>
            
            <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
              {message.content}
            </div>
            
            {message.data_points && message.data_points.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {message.data_points.map((point, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-white text-xs rounded-full border text-gray-600"
                  >
                    {point}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center justify-center p-4 text-gray-500">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            <span>Bots are analyzing real data and preparing responses...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask any sports question... (e.g., 'Who's better: Mahomes or Josh Allen?')"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>{isLoading ? 'Starting...' : 'Start Debate'}</span>
          </button>
        </form>
      </div>
    </div>
  )
} 