'use client'

import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | string // team themes

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  favoriteTeam: string | null
  setFavoriteTeam: (team: string) => void
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')
  const [favoriteTeam, setFavoriteTeam] = useState<string | null>(null)

  // Apply team theme when favorite team is set
  useEffect(() => {
    if (favoriteTeam) {
      setTheme(favoriteTeam.toLowerCase())
    }
  }, [favoriteTeam])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, favoriteTeam, setFavoriteTeam }}>
      <div className={`theme-${theme}`} data-theme={theme}>
        {children}
      </div>
    </ThemeContext.Provider>
  )
}
