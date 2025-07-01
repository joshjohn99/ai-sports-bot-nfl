'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'

interface ChatMessage {
  type: 'text' | 'rich-card' | 'carousel' | 'stats'
  content: any
  sender: 'user' | 'ai'
  timestamp: Date
}

export default function SportsChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  const suggestedQuestions = [
    "Compare Josh Allen vs Lamar Jackson passing stats",
    "Who has the most touchdowns this season?",
    "Show me Ravens vs Chiefs head-to-head",
    "Analyze Mahomes performance under pressure"
  ]

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b p-4">
        <h1 className="text-2xl font-bold">AI Sports Analyst</h1>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <WelcomeScreen suggestions={suggestedQuestions} />
        ) : (
          <MessageList messages={messages} />
        )}
      </div>

      {/* Input Area */}
      <ChatInput 
        value={input}
        onChange={setInput}
        onSend={handleSend}
        isTyping={isTyping}
        suggestions={isTyping ? [] : suggestedQuestions}
      />
    </div>
  )
}
