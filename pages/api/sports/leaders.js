export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, error: 'Method not allowed' })
  }

  try {
    const { sport = 'NFL', metric = 'yards', position, team, limit = 10, season } = req.query

    console.log(`🏈 API called: sport=${sport}, metric=${metric}, limit=${limit}`)

    // Proxy to your Python backend
    const backendUrl = `http://localhost:8000/api/league-leaders?sport=${sport}&metric=${metric}&limit=${limit}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 5000,
    })

    if (response.ok) {
      const data = await response.json()
      return res.status(200).json(data)
    } else {
      console.log('Backend response not OK:', response.status)
      throw new Error(`Backend error: ${response.status}`)
    }

  } catch (error) {
    console.error('API Error:', error.message)
    return res.status(500).json({ success: false, error: error.message })
  }
}
