"use client"

import { AiOutlineRise } from "react-icons/ai";
import { MdAccountBalance, MdCardTravel } from "react-icons/md";
import { LuWallet } from "react-icons/lu";

import { LineChart } from "./line-chart";

interface AccountCardProps {
  title: string,
  value: number,
  percentChange: string
  index: number
}

const icons = [
  {
    icon: MdAccountBalance
  },
  {
    icon: LuWallet
  },
  {
    icon: MdCardTravel
  }
]

export const AccountCard = (
  { title, value, percentChange, index }: AccountCardProps
) => {

  const selectedIcon = icons[index]
  const formattedVal = value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  return (
    <div className={`p-4 border border-muted-foreground/30 rounded-lg w-[250px] flex flex-col gap-2 ${index === 0 && "bg-[#5b44cc] dark:bg-[#3c2e8b] shadow-black/25"}  text-xs shadow-lg relative`}>
      <selectedIcon.icon
        size={28}
        className={`${index === 0 ? "text-white" : "text-muted-foreground"} absolute right-4 top-4`}
      />

      <p className={`${index === 0 ? "text-white/90" : "text-muted-foreground"} font-semibold`}>
        {title}
      </p>
      <p className={`${index === 0 && "text-white"} font-semibold text-xl mt-1`}>
        ${formattedVal}
      </p>

      <div className={`${index === 0 && "text-white"} flex items-end justify-between mt-2`}>
        <div className={`flex items-center justify-center gap-1  rounded-2xl py-1 px-2 bg-zinc-300/30 dark:bg-zinc-300/15 ${index === 1 && "text-green-600 bg-green-600/10 dark:bg-green-600/10"} ${index === 2 && "text-green-600 bg-green-600/10 dark:bg-red-600/10"}`}>
          <AiOutlineRise
            size={16}
          />
          <p className="font-medium text-[10px]">+30.23%</p>
        </div>
        <LineChart />
      </div>
    </div>
  )
}

