import { useState } from 'react'

export function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark')
  function choose(next: 'dark' | 'light') {
    document.documentElement.dataset.theme = next
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', next === 'dark' ? '#17191b' : '#f4f4ef')
    setTheme(next)
    try { localStorage.setItem('email-to-order-theme', next) } catch { /* The theme still works when browser storage is unavailable. */ }
  }
  return <div className="theme-toggle" role="group" aria-label="Colour theme">
    <button type="button" aria-pressed={theme === 'dark'} onClick={() => choose('dark')}>Dark</button>
    <button type="button" aria-pressed={theme === 'light'} onClick={() => choose('light')}>Light</button>
  </div>
}
