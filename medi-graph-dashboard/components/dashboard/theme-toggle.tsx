'use client'

import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark' | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check localStorage or system preference
    const stored = localStorage.getItem('theme')
    const isDark = stored
      ? stored === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches

    setTheme(isDark ? 'dark' : 'light')
    applyTheme(isDark ? 'dark' : 'light')
  }, [])

  const applyTheme = (newTheme: 'light' | 'dark') => {
    const html = document.documentElement
    html.classList.remove('light', 'dark')
    html.classList.add(newTheme)
  }

  const toggleTheme = () => {
    if (!theme) return

    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
  }

  if (!mounted) return null

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded border border-border hover:bg-secondary transition-colors"
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <Moon className="w-4 h-4 text-foreground" />
      ) : (
        <Sun className="w-4 h-4 text-foreground" />
      )}
    </button>
  )
}
