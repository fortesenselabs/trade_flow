import { create } from 'zustand'

interface OrderType {
  order: string
  setOrder: (order: string) => void
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
}

export const useOrder = create<OrderType>((set) => ({
  order: '0',
  setOrder: (order) => set({ order }),
  isOpen: false,
  setIsOpen: (isOpen) => set({ isOpen })
}))