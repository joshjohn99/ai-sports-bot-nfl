'use client'

import { useEffect, useState, useCallback } from 'react'
import useEmblaCarousel from 'embla-carousel-react'
import { AlertCircle, TrendingUp, Trophy, Target, ChevronLeft, ChevronRight } from 'lucide-react'

// TypeScript interfaces matching your backend models
interface PlayerStats {
  // Common stats
  games_played?: number
  games_started?: number
  
  // NFL stats
  passing_yards?: number
  passing_touchdowns?: number
  rushing_yards?: number
  rushing_touchdowns?: number
  receiving_yards?: number
  receptions?: number
  receiving_touchdowns?: number
  sacks?: number
  tackles?: number
  interceptions?: number
  
  // NBA stats
  points?: number
  rebounds?: number
  assists?: number
  steals?: number
  blocks?: number
  three_pointers_made?: number
}

interface Player {
  id: number
  external_id: string
  name: string
  position: string
  sport: string
  current_team?: {
    id: number
    name: string
    display_name: string
    abbreviation: string
  }
  stats?: PlayerStats
  image?: string
}

interface CarouselProps {
  sport?: string
  position?: string
  team?: string
  metric?: string
  limit?: number
  title?: string
}

interface ApiResponse {
  success: boolean
  data?: Player[]
  error?: string
  metadata?: {
    sport: string
    total: number
    position?: string
  }
}

export function SportsCarousel({ 
  sport = 'NFL', 
  position, 
  team, 
  metric = 'yards', 
  limit = 10,
  title = 'Top Performers'
}: CarouselProps) {
  const [emblaRef, emblaApi] = useEmblaCarousel({ 
    loop: false, 
    align: 'start',
    dragFree: true,
    containScroll: 'trimSnaps'
  })
  
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [canScrollPrev, setCanScrollPrev] = useState(false)
  const [canScrollNext, setCanScrollNext] = useState(false)

  // API call to your backend
  const fetchPlayers = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams({
        sport,
        metric,
        limit: limit.toString(),
        ...(position && { position }),
        ...(team && { team })
      })
      
      // Call your Python backend through Next.js API route
      const response = await fetch(`/api/sports/leaders?${params}`)
      const data: ApiResponse = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch players')
      }
      
      if (data.success && data.data) {
        setPlayers(data.data)
      } else {
        throw new Error(data.error || 'No players data received')
      }
      
    } catch (err) {
      console.error('Error fetching players:', err)
      setError(err instanceof Error ? err.message : 'Failed to load players')
      
      // Fallback to sample data for development
      setPlayers(getSamplePlayers(sport))
    } finally {
      setLoading(false)
    }
  }, [sport, position, team, metric, limit])

  // Scroll handlers
  const scrollPrev = useCallback(() => {
    if (emblaApi) emblaApi.scrollPrev()
  }, [emblaApi])

  const scrollNext = useCallback(() => {
    if (emblaApi) emblaApi.scrollNext()
  }, [emblaApi])

  const onSelect = useCallback(() => {
    if (!emblaApi) return
    setCanScrollPrev(emblaApi.canScrollPrev())
    setCanScrollNext(emblaApi.canScrollNext())
  }, [emblaApi])

  useEffect(() => {
    if (!emblaApi) return
    onSelect()
    emblaApi.on('select', onSelect)
    emblaApi.on('reInit', onSelect)

    return () => {
      emblaApi.off('select', onSelect)
      emblaApi.off('reInit', onSelect)
    }
  }, [emblaApi, onSelect])

  useEffect(() => {
    fetchPlayers()
  }, [fetchPlayers])

  if (loading) {
    return <CarouselSkeleton />
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-8 text-center">
        <div className="space-y-4">
          <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
          <div>
            <h3 className="font-semibold">Failed to load players</h3>
            <p className="text-sm text-gray-600">{error}</p>
            <button 
              onClick={fetchPlayers} 
              className="mt-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
          <p className="text-gray-600">
            {sport} {position && `${position} `}leaders by {metric}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            onClick={scrollPrev}
            disabled={!canScrollPrev}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            onClick={scrollNext}
            disabled={!canScrollNext}
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Carousel */}
      <div className="overflow-hidden" ref={emblaRef}>
        <div className="flex gap-4">
          {players.map((player, index) => (
            <div key={player.id || index} className="flex-[0_0_320px]">
              <PlayerCard 
                player={player} 
                rank={index + 1}
                sport={sport}
                metric={metric}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Enhanced Player Card Component
function PlayerCard({ 
  player, 
  rank, 
  sport, 
  metric
}: { 
  player: Player
}) {
  const getPrimaryStatValue = () => {
    if (!player.stats) return 0;

    const statMap: Record<string, keyof PlayerStats> = {
      // NFL
      'yards': sport === 'NFL'
        ? (player.position === 'QB'
            ? 'passing_yards'
            : player.position === 'RB'
              ? 'rushing_yards'
              : 'receiving_yards')
        : 'points',
      'touchdowns': sport === 'NFL'
        ? (player.position === 'QB'
            ? 'passing_touchdowns'
            : player.position === 'RB'
              ? 'rushing_touchdowns'
              : 'receiving_touchdowns')
        : 'points',
      'sacks': 'sacks',
      'tackles': 'tackles',
      'interceptions': 'interceptions',

      // NBA
      'points': 'points',
      'rebounds': 'rebounds',
      'assists': 'assists',
      'steals': 'steals',
      'blocks': 'blocks'
    }

    const statKey = statMap[metric] || 'passing_yards'
    return player.stats[statKey] || 0
  }

  // Get supporting stats based on sport
  const getSupportingStats = () => {
    if (!player.stats) return []
    
    if (sport === 'NFL') {
      return [
        { label: 'Games', value: player.stats.games_played || 0 },
        { label: 'TDs', value: (player.stats.passing_touchdowns || 0) + (player.stats.rushing_touchdowns || 0) },
        { label: 'Yards', value: (player.stats.passing_yards || 0) + (player.stats.rushing_yards || 0) }
      ]
    } else if (sport === 'NBA') {
      return [
        { label: 'PPG', value: player.stats.points || 0 },
        { label: 'RPG', value: player.stats.rebounds || 0 },
        { label: 'APG', value: player.stats.assists || 0 }
      ]
    }
    
    return []
  }

  const primaryValue = getPrimaryStatValue()
  const supportingStats = getSupportingStats()

  return (
    <div className="relative overflow-hidden bg-white rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 group">
      {/* Rank Badge */}
      <div className="absolute top-4 left-4 z-10">
        <span 
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            rank <= 3 ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black' : 'bg-gray-100 text-gray-800'
          }`}
        >
          #{rank}
        </span>
      </div>

      {/* Player Image */}
      <div className="aspect-video relative bg-gradient-to-br from-gray-100 to-gray-200">
        {player.image ? (
          <img 
            src={player.image} 
            alt={player.name}
            className="object-cover w-full h-full"
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-6xl font-bold text-gray-300">
              {/* Defensive initials generation */}
              {(() => {
                if (!player.name || typeof player.name !== 'string') return '?';
                const parts = player.name.trim().split(/\s+/).filter(Boolean);
                if (parts.length === 0) return '?';
                if (parts.length === 1) return parts[0][0]?.toUpperCase() || '?';
                // For multi-part names, use first char of first and last part
                const first = parts[0][0]?.toUpperCase() || '';
                const last = parts[parts.length - 1][0]?.toUpperCase() || '';
                return (first + last) || '?';
              })()}
            </div>
          </div>
        )}
        
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        
        {/* Player Info Overlay */}
        <div className="absolute bottom-4 left-4 text-white">
          <h3 className="font-bold text-xl group-hover:scale-105 transition-transform">
            {player.name}
          </h3>
          <div className="flex items-center gap-2 text-sm opacity-90">
            <span>{player.position}</span>
            {player.current_team && (
              <>
                <span>•</span>
                <span>{player.current_team.abbreviation}</span>
              </>
            )}
          </div>
        </div>

        {/* Primary Stat */}
        <div className="absolute top-4 right-4 text-white text-right">
          <div className="text-2xl font-bold">{primaryValue.toLocaleString()}</div>
          <div className="text-xs opacity-75 uppercase">{metric}</div>
        </div>
      </div>

      <div className="p-4">
        {/* Supporting Stats */}
        <div className="grid grid-cols-3 gap-4 text-center mb-4">
          {supportingStats.map((stat, index) => (
            <div key={index}>
              <div className="font-bold text-lg">{stat.value.toLocaleString()}</div>
              <div className="text-xs text-gray-600">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Action Button */}
        <button className="w-full px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center justify-center gap-2">
          <Target className="h-4 w-4" />
          Compare Player
        </button>
      </div>
    </div>
  )
}

// Loading skeleton
function CarouselSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-2">
          <div className="h-10 w-10 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-10 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
      
      <div className="flex gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex-[0_0_320px]">
            <div className="bg-white rounded-lg shadow">
              <div className="aspect-video w-full bg-gray-200 rounded-t-lg animate-pulse" />
              <div className="p-4">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <div key={j} className="text-center">
                      <div className="h-6 w-12 mx-auto mb-1 bg-gray-200 rounded animate-pulse" />
                      <div className="h-3 w-8 mx-auto bg-gray-200 rounded animate-pulse" />
                    </div>
                  ))}
                </div>
                <div className="h-10 w-full bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function getSamplePlayers(sport: string): Player[] {
  // Fallback sample data for development
  const samples = {
    'NFL': [
      {
        id: 1,
        external_id: '1',
        name: 'Patrick Mahomes',
        position: 'QB',
        sport: 'NFL',
        current_team: { id: 1, name: 'Kansas City Chiefs', display_name: 'Chiefs', abbreviation: 'KC' },
        stats: { passing_yards: 4183, passing_touchdowns: 27, games_played: 17 }
      },
      {
        id: 2,
        external_id: '2',
        name: 'Josh Allen',
        position: 'QB',
        sport: 'NFL',
        current_team: { id: 2, name: 'Buffalo Bills', display_name: 'Bills', abbreviation: 'BUF' },
        stats: { passing_yards: 4306, passing_touchdowns: 29, games_played: 17 }
      }
    ],
    'NBA': [
      {
        id: 1,
        external_id: '1',
        name: 'LeBron James',
        position: 'SF',
        sport: 'NBA',
        current_team: { id: 1, name: 'Los Angeles Lakers', display_name: 'Lakers', abbreviation: 'LAL' },
        stats: { points: 25, rebounds: 7, assists: 8, games_played: 55 }
      }
    ]
  }
  
  return samples[sport as keyof typeof samples] || []
}