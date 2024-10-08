"use client"
import { Progress } from "@/components/shadcn-ui/progress"
import { Company } from "@prisma/client"
import { useEffect, useState } from "react"
import BigNumber from 'bignumber.js'

interface ProgressBarProps {
  company: Company
}

const getPortion = (portion: number) => {
  // raging from 0 to 1000
  if (portion > 0 && portion < 10) return 10;
  if (portion > 10 && portion < 50) return 20;
  if (portion > 50 && portion < 150) return 50;
  if (portion >= 150 && portion < 300) return 56;
  if (portion > 300 && portion < 600) return 70;
  if (portion > 600 && portion < 900) return 85;
  else return 90
}

const getPortion2 = (portion: number) => {
  // raging from 0 to 1000
  if (portion > 0 && portion < 10) return 10;
  if (portion > 10 && portion < 50) return 20;
  if (portion > 50 && portion < 150) return 50;
  if (portion >= 150 && portion < 300) return 56;
  if (portion > 300 && portion < 600) return 70;
  if (portion > 600 && portion < 900) return 85;
  else return 90
}

export function ProgressBar({ company }: ProgressBarProps) {
  const [progress, setProgress] = useState(0)
  const [secondProgress, setSecondProgress] = useState(0)
  const revenue = new BigNumber(company.yahooStockV2Summary.financialData.totalRevenue.raw)
  const formatRevenue = revenue.toFormat(0, { groupSeparator: ',', groupSize: 3 })

  const total = new BigNumber(1000000000)
  const portion = revenue.dividedBy(total).toNumber()

  const marketCap = new BigNumber(company.yahooStockV2Summary.price.marketCap.raw)
  const formatRevenue2 = marketCap.toFormat(0, { groupSeparator: ',', groupSize: 3 })
  const totalMarket = new BigNumber(100000000)
  const portion2 = revenue.dividedBy(totalMarket).toNumber()

  useEffect(() => {
    setProgress(getPortion(portion));
    setSecondProgress(getPortion2(portion2))
  }, [company])

  return (
    <div>
      <div className="flex justify-between w-[75%] text-xs mb-1">
        <p className="text-[10px] text-muted-foreground">Market Capitalization</p>
        <p>${formatRevenue2}</p>
      </div>
      <Progress
        value={secondProgress}
        className="w-[75%] h-[5px]"
      />

      <div className="flex justify-between w-[75%] text-xs mb-1 mt-3">
        <p className="text-[10px] text-muted-foreground">2023 Revenue</p>
        <p>${formatRevenue}</p>
      </div>
      <Progress
        value={progress}
        className="w-[75%] h-[5px]"
      />
    </div>
  )
}
