import { create } from 'zustand'

interface ITicker {
  ticker: string
  setTicker: (ticker: string) => void
  isLiking: boolean
  setIsLiking: (isLiking: boolean) => void
}

export const useTicker = create<ITicker>((set) => ({
  ticker: 'MSFT',
  setTicker: (ticker) => set({ ticker }),
  isLiking: false,
  setIsLiking: (isLiking) => set({ isLiking })
}))