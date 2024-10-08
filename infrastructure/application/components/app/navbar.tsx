"use client"

import { UserButton } from "@clerk/nextjs"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { ThemeSwitch } from "./theme-switch"

const getName = (pathName: string): string => {
  if (pathName.includes("dashboard")) return "Dashboard"
  else if (pathName.includes("market")) return "Market"
  else return "Messenger"
}

export function Navbar() {

  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])
  if (!isClient) {
    return;
  }
  const pathName = usePathname();
  const name = getName(pathName)
  return (
    <div className="flex items-center justify-between flex-1 px-6 h-[60px] border-b border-muted-foreground/30 bg-white dark:bg-[#020817]">
      <p className="text-lg font-semibold">
        {name}
      </p>

      <div className="flex items-center gap-4">
        <ThemeSwitch />
        <UserButton afterSignOutUrl="/" />
      </div>
    </div>
  )
}
