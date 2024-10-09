import { Label } from "@/components/shadcn-ui/label"
import toast from "react-hot-toast"
import { Button } from "@/components/shadcn-ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogOverlay
} from "@/components/shadcn-ui/dialog"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/shadcn-ui/card"
import { cn } from "@/lib/utils"
import { useState } from "react"
import { Card as CardModel } from "@prisma/client"
import { CardContent as CardContainer } from "./card-content"
import { Separator } from "@/components/shadcn-ui/separator"

interface ViewCardsProps {
  cardLists: CardModel[]
}

export const ViewCards = ({ cardLists }: ViewCardsProps) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <DialogContent className="min-w-[500px] h-[600px] pt-[40px] pb-[20px] ">
      <div className="flex justify-center w-full">
        <Card className="w-[450px]">
          <CardHeader>
            <CardTitle>Available Cards</CardTitle>
            <CardDescription>manage your cards under my cards section.</CardDescription>
          </CardHeader>
          <CardContent>
            <Separator />
            <div className="w-full flex flex-col gap-4 items-center  pt-8 max-h-[410px] overflow-y-auto">
              {cardLists.map((item) =>
                <CardContainer className="w-[300px]" cardData={item} />
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </DialogContent>

  )
}