import { create } from 'zustand'

interface IColor {
  color: string
  setColor: (color: string) => void
}

export const useColor = create<IColor>((set) => ({
  color: '#286662',
  setColor: (color: string) => { set({ color }) },
}))