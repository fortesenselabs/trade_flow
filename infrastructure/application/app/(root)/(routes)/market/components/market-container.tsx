"use client"

import { useAnimate } from "framer-motion"
import { useEffect } from "react"

import { useAnimation } from "@/hooks/use-animation"
import { useTicker } from "@/hooks/use-ticker"
import { Company } from "@prisma/client"
import { CompanyProfile } from "./company-profile/company-profile"
import { FeaturedProduct } from "./products/featured-product"
import TableContainer from "./table/table-container"
export interface MarketContainerProps {
  companies: Company[]
}

const MarketContainer = ({ companies }: MarketContainerProps) => {
  const { ticker } = useTicker()
  const foundCompany = companies.find((item: Company) => item.symbol === ticker)
  const updatedAt = new Date(foundCompany.yahooStockV2Summary.price.regularMarketTime).toLocaleTimeString()
  const { animatedId, setAnimatedId, firstLoop, setFirstLoop } = useAnimation()
  const [frontElement, animate] = useAnimate();
  const [behindElement, animate1] = useAnimate();
  // Animation
  useEffect(() => {
    if (firstLoop) {
      setFirstLoop(false);
      return;
    }
    if (animatedId === 1) {
      console.log(animatedId)
      const windowWidth = window.innerWidth;
      const xValue = -65 * (windowWidth / 100);
      animate(frontElement.current, { opacity: 0, scale: .8, x: xValue }, { duration: .2 });
      animate1(behindElement.current, { scale: [.8, 1], x: [-xValue, 0] }, { duration: .2 });
    }
    if (animatedId === 2) {
      const windowWidth = window.innerWidth;
      const xValue = 65 * (windowWidth / 100);
      animate(frontElement.current, { opacity: 1, scale: 1, x: 0 }, { duration: .2 });
      animate1(behindElement.current, { scale: [1, .8], x: xValue }, { duration: .2 });
    }
  }, [animatedId, firstLoop])
  // useEffect(() => {
  //   setAnimatedId(2)
  // }, [pathname])
  return (
    <div className="flex h-full">
      {/*Left Container*/}
      <div className="w-[35%] pt-8 pb-12 px-8 border-r border-muted-foreground/30">
        <FeaturedProduct
          company={foundCompany}
        />
      </div>

      {/*Right Container*/}
      <div className={`relative flex-1 overflow-hidden ${animatedId === 1 && "overflow-y-auto"}`} >
        <div
          ref={frontElement}
          className={`absolute pt-8 z-[1] w-full h-full flex flex-col overflow-y-auto ${animatedId === 1 && "opacity-0"}`}
        >
          <div className="flex items-end justify-between gap-4 px-8 pb-6 text-lg font-semibold">
            <p>Companies</p>
            <div className="text-[11px] font-medium text-muted-foreground ">
              Updated {updatedAt}
            </div>
          </div>
          <div className="flex-1 ">
            <TableContainer companies={companies} />
          </div>
        </div>

        <div
          ref={behindElement}
          className={`absolute flex-1 w-full h-full ${animatedId === 2 && "opacity-0"}`}
        >
          <CompanyProfile
            company={foundCompany}
          />
        </div>
      </div>
    </div>
  )
}

export default MarketContainer