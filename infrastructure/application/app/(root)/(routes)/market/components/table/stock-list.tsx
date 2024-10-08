"use client"

import Image from "next/image";

import { SearchInput } from "./search-input";
import { MdCorporateFare } from "react-icons/md";
import { LiaIndustrySolid } from "react-icons/lia";
import { MdCurrencyExchange } from "react-icons/md";
import { BsPeople } from "react-icons/bs";
import { MoveRight } from "lucide-react";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/shadcn-ui/table";
import { Company } from "@prisma/client";

interface StockListProps {
  ticker: string
  setTicker: (ticker: string) => void
  companies: Company[]
  animatedClick: () => void;
  searchSymbol: string
}


const getSentimentalColor = (input: string) => {
  switch (input) {
    case "strong buy":
      return "text-green-500";
    case "buy":
      return "text-green-600";
    case "sell":
      return "text-red-600";
    case "strong sell":
      return "text-red-500";
    default:
      return "text-blue-500";
  }
};

const getChangeFormat = (percent: number) => {
  if (percent < 0) return percent.toFixed(2) + '%'
  return '+' + percent.toFixed(2) + '%'
}

export const StockList = ({ ticker, setTicker, companies, animatedClick }: StockListProps) => {


  const handleClick = (company: Company) => {
    // Call back func
    setTicker(company.symbol);
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <SearchInput />
        <div className="flex items-center justify-center h-full px-4 py-2">
          <p className="text-xs text-muted-foreground"> Results</p>
        </div>
      </div>
      <Table>
        <TableCaption>
          <p>A list of top ranked companies.</p>
        </TableCaption>
        <TableHeader >
          <TableRow>
            {/* <TableHead className=" w-[50px]">
              <div className="flex items-start gap-0.5">
                <GiRank3
                  size={16}
                  className="text-black"
                />
                <p>Rank</p>
              </div>
            </TableHead> */}
            <TableHead className=" w-[150px]">
              <div className="flex items-start gap-0.5">
                <MdCorporateFare
                  size={16}
                  className="text-black"
                />
                <p>Company</p>
              </div>
            </TableHead>
            <TableHead className="w-[200px]">
              <div className="flex items-start gap-0.5">
                <LiaIndustrySolid
                  size={16}
                  className="text-black"
                />
                <p>Sector</p>
              </div>
            </TableHead>
            <TableHead className="">
              <div className="flex items-start gap-0.5">
                <BsPeople
                  size={16}
                  className="text-black"
                />
                <p className="">Trend</p>
              </div>
            </TableHead>
            <TableHead className="">
              <div className="flex items-start gap-0.5">
                <MdCurrencyExchange
                  size={16}
                  className="text-black"
                />
                <p>Price</p>
              </div>
            </TableHead>
            <TableHead className="">
              <div className="flex items-start gap-0.5">
                <MdCurrencyExchange
                  size={16}
                  className="text-black"
                />
                <p>Chg</p>
              </div>
            </TableHead>

          </TableRow>
        </TableHeader>
        <TableBody>
          {companies
            .map((item: Company, index: number) => (
              <TableRow
                key={index}
                onClick={() => handleClick(item)}
                className={`
                        border-t-2
                        border-t-muted-foreground/20
                          text-xs
                          font-medium
                          hover:bg-indigo-600/10
                          hover:cursor-pointer
                          ${item.symbol === ticker && 'border-2 border-indigo-600'}
                          `}
              >
                {/* <TableCell className="font-medium">
                <div className="flex items-center justify-center">
                  {item.rank}
                </div>
              </TableCell> */}
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className={`flex items-center justify-center w-[28px] h-[28px] rounded-full `}>
                      <Image
                        src={item.logo.logo.toLowerCase()}
                        alt="logo"
                        width={28}
                        height={28}
                        className="max-h-[18px]"
                      />
                    </div>
                    {item.symbol}
                  </div>
                </TableCell>
                <TableCell className="">
                  <p>{item.yahooStockV2Summary.summaryProfile.sector}</p>
                </TableCell>
                <TableCell className={`${getSentimentalColor(item.yahooStockV2Summary.financialData.recommendationKey)}`}>
                  {item.yahooStockV2Summary.financialData.recommendationKey}
                </TableCell>
                <TableCell className="">
                  ${item.price}
                </TableCell>
                <TableCell className={`${item.yahooMarketV2Data.regularMarketChangePercent > 0 ? "text-green-500" : "text-red-500"}`}>
                  {getChangeFormat(item.yahooMarketV2Data.regularMarketChangePercent)}
                </TableCell>
                <TableCell className="w-[50px]">
                  {item.symbol === ticker &&
                    <button
                      className="px-2 py-[2px] border rounded-lg border-muted-foreground"
                      onClick={animatedClick}
                    >
                      <MoveRight
                        size={16}
                        className="ml-1"
                      />
                    </button>
                  }
                </TableCell>
              </TableRow>
            ))}
        </TableBody>
      </Table>
    </div>

  )
}
