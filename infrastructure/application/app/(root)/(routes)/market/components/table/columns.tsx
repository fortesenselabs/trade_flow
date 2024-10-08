"use client"

import Image from "next/image"
import { ColumnDef } from "@tanstack/react-table"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { DataTableColumnHeader } from "./column-header"
import { MoveRight } from "lucide-react"
import { useTicker } from "@/hooks/use-ticker"
import { useAnimation } from "@/hooks/use-animation"
import { Button } from "@/components/aceternity-ui/moving-border"

// This type is used to define the shape of our data.
export type CompanyDef = {
  symbol: string,
  sector: string,
  trend: string,
  price: number,
  percentChg: number
}

export const columns: ColumnDef<CompanyDef>[] = [
  {
    accessorKey: "symbol",
    header: ({ column }) => (
      <div className="w-[70px]"><DataTableColumnHeader column={column} title="Company" /></div>
    ),
    cell: ({ row }) => {

      const data: string = row.getValue("symbol")
      const imgPath = "/logos/" + data.toLowerCase() + ".svg";
      return (
        <div className="flex gap-3 items-center text-xs w-[70px]">
          <Image
            src={imgPath}
            alt="Company logo"
            width={18}
            height={18}
          />
          {data}
        </div>
      )
    }
  },
  {
    accessorKey: "sector",
    header: ({ column }) => (
      <div className=""><DataTableColumnHeader column={column} title="Sector" /></div>
    ),
    cell: ({ row }) => {
      return <div className="">{row.getValue("sector")}</div>
    },
  },
  {
    accessorKey: "trend",
    header: ({ column }) => (
      <div className="w-[75px]"><DataTableColumnHeader column={column} title="Trend" /></div>
    ),
    cell: ({ row }) => {
      const data = row.getValue("trend")
      return (
        <div className={`w-[75px] ${data === "buy" ?
          "text-green-500" :
          data === "hold" ?
            "text-blue-500" :
            "text-red-600"}`}>
          {row.getValue("trend")}
        </div>
      )
    },
  },
  {
    accessorKey: "price",
    header: ({ column }) => (
      <div className=""><DataTableColumnHeader column={column} title="Price" /></div>
    ),
    cell: ({ row }) => {
      const amount = parseFloat(row.getValue("price"))
      const formatted = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(amount)

      return <div>{formatted}</div>
    },

  },
  {
    accessorKey: "percentChg",
    header: ({ column }) => (
      <div className="w-[100px]"><DataTableColumnHeader column={column} title="Change" /></div>
    ),
    cell: ({ row }) => {
      const data = parseFloat(row.getValue("percentChg"))
      const { animatedId, setAnimatedId } = useAnimation();

      const { ticker } = useTicker()
      const style = data < 0 ? "text-red-400" : "text-green-400";
      return (
        <div className="flex items-center justify-between">
          <p className={`w-[60px] ${style}`}>
            {data < 0 ? data.toFixed(2) + "%" : '+' + data.toFixed(2) + '%'}
          </p>
          {ticker === row.getValue("symbol") && <Button
            onClick={() => {
              setAnimatedId(1)
            }}
            borderRadius="100px"
            className={cn("text-black bg-white dark:bg-slate-900 hover:bg-cyan-800 hover:text-white dark:text-white border-neutral-400 dark:border-slate-800")}
          >
            <MoveRight
              size={16}
              className="ml-1"
            />
          </Button>}
        </div>

      )


    }
  }
]
