import { create } from 'zustand'

interface IAnimation {
  animatedId: number
  setAnimatedId: (animatedId: number) => void
  firstLoop: boolean
  setFirstLoop: (firstLoop: boolean) => void,
}

export const useAnimation = create<IAnimation>((set) => ({
  animatedId: 2,
  setAnimatedId: (animatedId) => set({ animatedId }),
  firstLoop: true,
  setFirstLoop: (firstLoop: boolean) => { set({ firstLoop }) },
}))