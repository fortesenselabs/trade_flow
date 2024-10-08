import { create } from 'zustand'

interface IAccount {
  accountVal: number
  setAccountVal: (accountVal: number) => void
}

export const useAccount = create<IAccount>((set) => ({
  accountVal: 0,
  setAccountVal: (accountVal: number) => { set({ accountVal }) },
}))