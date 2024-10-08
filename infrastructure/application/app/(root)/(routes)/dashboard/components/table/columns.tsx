"use client"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"
import { ColumnDef } from "@tanstack/react-table"
import { ColumnHeader } from "./column-header"

import { Button } from "@/components/shadcn-ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/shadcn-ui/dropdown-menu"
import { Checkbox } from "@/components/shadcn-ui/checkbox"
import { Transaction } from "@prisma/client"
import Image from "next/image"


export const columns: ColumnDef<Transaction>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      return (
        <div className={`border border-muted-foreground/30 rounded-xl text-[10px] flex justify-center font-semibold
        ${row.getValue('status') === 'success' ? ' text-green-600' : ' text-red-600'} `}>
          {row.getValue('status')}
        </div>
      )
    }
  },
  {
    // key: the data model collumn name
    accessorKey: "id",
    header: "Transaction ID"
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => {
      const type: string = row.getValue("type");
      const firstType = type.split(" ")[0]
      return (
        <div className={`${(firstType === 'buy' || type === 'deposit') ? "text-green-500" : "text-red-500"
          } font-medium `}>
          {type}
        </div>)
    }
  },
  {
    accessorKey: "amount",
    header: "Amount",
    cell: ({ row }) => {
      const type: string = row.getValue("type");
      const firstType = type.split(" ")[0]
      const operator = (type === 'withdraw' || firstType === 'buy') ? '-' : '+';
      return <div>{operator}${row.getValue('amount')}</div>
    }
  },
  {
    accessorKey: "createdAt",
    header: "Date",
    cell: ({ row }) => {
      const value = new Date(row.getValue('createdAt'))
      return <div>{value.toLocaleString()}</div>
    }
  },

]
