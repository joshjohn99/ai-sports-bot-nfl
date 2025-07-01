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
    
    // Return mock data as fallback
    const mockData = {
      success: true,
      data: [
        { id: 1, name: "Patrick Mahomes", team: "KC", position: "QB", stats: { yards: 4183 }},
        { id: 2, name: "Josh Allen", team: "BUF", position: "QB", stats: { yards: 4306 }},
        { id: 3, name: "T.J. Watt", team: "PIT", position: "LB", stats: { yards: 0 }},
        { id: 4, name: "Myles Garrett", team: "CLE", position: "DE", stats: { yards: 0 }}
      ],
      metadata: { sport: req.query.sport || 'NFL',
        metric,
        total: mockData.data.length,
        source: 'mock_data'
      }
    }

    res.status(200).json(mockData)
  }
}

function getSampleData(sport, limit) {
  const samples = {
    'NFL': [
      {
        id: 1,
        external_id: '1',
        name: 'Patrick Mahomes',
        position: 'QB',
        sport: 'NFL',
        current_team: { 
          id: 1, 
          name: 'Kansas City Chiefs', 
          display_name: 'Chiefs', 
          abbreviation: 'KC' 
        },
        stats: { 
          passing_yards: 4183, 
          passing_touchdowns: 27, 
          games_played: 17,
          sacks: 0,
          tackles: 0,
          interceptions: 0
        }
      },
      {
        id: 2,
        external_id: '2',
        name: 'Josh Allen',
        position: 'QB',
        sport: 'NFL',
        current_team: { 
          id: 2, 
          name: 'Buffalo Bills', 
          display_name: 'Bills', 
          abbreviation: 'BUF' 
        },
        stats: { 
          passing_yards: 4306, 
          passing_touchdowns: 29, 
          games_played: 17,
          sacks: 0,
          tackles: 0,
          interceptions: 0
        }
      },
      {
        id: 3,
        external_id: '3',
        name: 'T.J. Watt',
        position: 'LB',
        sport: 'NFL',
        current_team: { 
          id: 3, 
          name: 'Pittsburgh Steelers', 
          display_name: 'Steelers', 
          abbreviation: 'PIT' 
        },
        stats: { 
          passing_yards: 0, 
          passing_touchdowns: 0, 
          games_played: 16,
          sacks: 19,
          tackles: 55,
          interceptions: 1
        }
      },
      {
        id: 4,
        external_id: '4',
        name: 'Myles Garrett',
        position: 'DE',
        sport: 'NFL',
        current_team: { 
          id: 4, 
          name: 'Cleveland Browns', 
          display_name: 'Browns', 
          abbreviation: 'CLE' 
        },
        stats: { 
          passing_yards: 0, 
          passing_touchdowns: 0, 
          games_played: 16,
          sacks: 14,
          tackles: 42,
          interceptions: 0
        }
      }
    ],
    'NBA': [
      {
        id: 1,
        external_id: '1',
        name: 'LeBron James',
        position: 'SF',
        sport: 'NBA',
        current_team: { 
          id: 1, 
          name: 'Los Angeles Lakers', 
          display_name: 'Lakers', 
          abbreviation: 'LAL' 
        },
        stats: { 
          points: 25, 
          rebounds: 7, 
          assists: 8, 
          games_played: 55,
          steals: 1,
          blocks: 1
        }
      },
      {
        id: 2,
        external_id: '2',
        name: 'Luka Dončić',
        position: 'PG',
        sport: 'NBA',
        current_team: { 
          id: 2, 
          name: 'Dallas Mavericks', 
          display_name: 'Mavericks', 
          abbreviation: 'DAL' 
        },
        stats: { 
          points: 32, 
          rebounds: 9, 
          assists: 8, 
          games_played: 70,
          steals: 1,
          blocks: 0
        }
      }
    ]
  }
  
  const sportData = samples[sport] || samples['NFL']
  return sportData.slice(0, limit)
} 