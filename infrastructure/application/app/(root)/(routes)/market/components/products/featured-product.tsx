"use client"

import { Company } from "@prisma/client";
import { useAnimate } from "framer-motion";
import Image from "next/image";
import { useEffect, useState } from "react";
import Wrapper from "../transaction/wrapper";
import Heart from "./heart";
import { ProductDialog } from "./product-dialog";
import { ProgressBar } from "./progress-bar";
import { useTicker } from "@/hooks/use-ticker";
interface FeaturedProductProps {
  company: Company,
}

export const FeaturedProduct: React.FC<FeaturedProductProps> = ({ company }) => {
  const { ticker } = useTicker()
  const [scope, animate] = useAnimate();
  const [scope2, animate2] = useAnimate();
  const [isSwapped, setIsSwapped] = useState(true)

  const companyName = company.yahooStockV2Summary.price.shortName
  // animate product img
  useEffect(() => {
    if (isSwapped) {
      animate(scope.current, { x: 150, scale: 0, opacity: 0 }, { duration: 0 })
      const timeout = setTimeout(() => {
        animate2(scope2.current, { x: 0, scale: 1, opacity: 1 }, { duration: .4 })
      }, 50)
      setIsSwapped(!isSwapped)
      return () => clearTimeout(timeout);
    }

    animate2(scope2.current, { x: 150, scale: 0, opacity: 0 }, { duration: 0 })
    const timeout2 = setTimeout(() => {
      animate(scope.current, { x: 0, scale: 1, opacity: 1 }, { duration: .4 })
    }, 50)
    setIsSwapped(!isSwapped)
    return () => clearTimeout(timeout2);
  }, [ticker])
  return (
    <div className="flex flex-col justify-between h-full text-sm">
      <div className="flex justify-between">
        <div>
          <p className="mb-1 text-lg font-semibold">
            {companyName}
          </p>
          <ProductDialog company={company} />
          <Heart />

        </div>
        <div className="flex flex-col items-end">
          <h1 className="flex text-lg font-semibold ">
            ${company.price} <span className="text-[10px] text-muted-foreground ml-1">/ea</span>
          </h1>
          <Wrapper company={company} />
        </div>
      </div>

      <div className="relative flex items-center justify-center flex-1 w-[300px] h-[300px] mx-auto">
        <Image
          className={"object-contain  absolute w-auto h-auto"}
          src={`/products/${ticker.toLowerCase()}.webp`}
          alt="Product Image"
          width={300}
          height={300}
          ref={scope}
          priority={true}
        />
        <Image
          className={"object-contain  absolute opacity-0 scale-[.2] translate-x-[150px] w-auto h-auto"}
          src={`/products/${ticker.toLowerCase()}.webp`}
          alt="Product Image"
          width={300}
          height={300}
          ref={scope2}
          priority={true}
        />
      </div>
      <div className="">
        <ProgressBar company={company} />
      </div>
    </div>
  )
}
