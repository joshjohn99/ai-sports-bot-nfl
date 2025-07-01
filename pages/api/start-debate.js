export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Method not allowed' })
  }

  try {
    const { question, user_id } = req.body

    console.log(`🏟️ Frontend requesting debate: ${question}`)

    // Call your real backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/start-debate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, user_id })
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    console.log(`✅ Real debate response received`)

    res.status(200).json(data)

  } catch (error) {
    console.error('❌ Debate API error:', error)
    res.status(500).json({
      success: false,
      error: error.message
    })
  }
} 