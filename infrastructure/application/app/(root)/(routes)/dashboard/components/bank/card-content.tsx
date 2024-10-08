import { cn } from "@/lib/utils"
import { Card } from "@prisma/client"
import { useQueryClient } from "@tanstack/react-query"

interface CardContentProps {
  className?: string,
  order?: string,
  cardData: Card
}

export const CardContent = ({ className, order, cardData }: CardContentProps) => {
  const firstData = cardData

  const visibleDigits = firstData.cardDigits.slice(0, 3);
  const lastTwoDigits = firstData.cardDigits.slice(-2);
  const hiddenDigits = "* **** **** **";
  const formattedCardNumber = visibleDigits + hiddenDigits + lastTwoDigits;
  return (
    <div className={cn("", className)}>
      <div
        style={{ backgroundColor: `${cardData.color}` }}
        className={`flex flex-col justify-between h-[164px] p-4 mt-4 text-xs border rounded-lg shadow-lg border-muted-foreground/30 bg-[#256662] text-white font-normal mx-2 `}>
        <p className="flex justify-between">
          {firstData.holderName}
          <span className="text-xl font-bold">VISA</span>
        </p>

        <div>
          <p className="mb-2 text-sm">{formattedCardNumber}</p>

          <p className="flex justify-between text-sm">
            ${firstData.value}
            <span>{firstData.expiration}</span>
          </p>
        </div>
      </div>
    </div>
  )
}

