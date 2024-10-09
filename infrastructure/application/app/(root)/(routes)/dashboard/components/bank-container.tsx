"use client"
import { DropdownContent } from "./bank/dropdown-content"
import { Wrapper } from "./bank/wrapper"
export function BankContainer() {
  return (
    <div className="w-full px-4 pt-4 pb-2">
      <div className="flex items-center justify-between w-full relative">
        <p className="text-sm font-semibold">My Cards</p>

        <DropdownContent />
      </div>
      <Wrapper />
    </div>
  )
}