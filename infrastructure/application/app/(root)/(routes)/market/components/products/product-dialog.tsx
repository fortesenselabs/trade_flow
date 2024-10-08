import { ExternalLink } from "lucide-react"
import { Button } from "@/components/shadcn-ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/shadcn-ui/dialog"
import Image from "next/image"
import { Separator } from "@/components/shadcn-ui/separator"
import { BarChart } from "./bar-chart"
import { Company } from "@prisma/client"

interface ProductDialogProps {
  company: Company
}

export const ProductDialog = ({ company }: ProductDialogProps) => {

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          className="flex gap-2 text-sm text-muted-foreground hover:underline"
        >
          <p>Revenue</p>
          <ExternalLink
            width={20}
            height={20}
          />
        </button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-[980px] overflow-hidden">
        <DialogHeader>
          <DialogTitle>{company.yahooStockV2Summary.price.shortName} Revenue/Earnings</DialogTitle>
          <DialogDescription>
            Earning charts helps you understand the performance of the company.
          </DialogDescription>
        </DialogHeader>
        <BarChart company={company} />
      </DialogContent>
    </Dialog>
  )
}
