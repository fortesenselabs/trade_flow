"use client"

import { Company } from "@prisma/client";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Heart } from "lucide-react";
import Image from "next/image";
export const Watchlist = () => {

  const { data, isLoading } = useQuery<Company[]>({
    queryKey: ['getWatchlist'],
    queryFn: async () => {
      const response = await axios.get('/api/watchlist')
      return response.data;
    },
    staleTime: 3600000 // 1 hour in ms only runs once when the component mounts
  })

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-[30px] text-muted-foreground'>
        ...Loading
      </div>
    );
  }
  return (
    <>
      {!data || data.length === 0 ?
        <div className="h-[30px] flex items-center justify-center text-muted-foreground text-sm">No watchlist added</div> :

        <div className="flex flex-col gap-3 mt-2">
          {data.map((company) => (
            <div
              key={company.id}
              className="flex justify-between px-4 py-2 text-xs rounded-md shadow-md "
            >
              <div className="flex items-center gap-2 w-[210px] ">
                <Image
                  alt="stock img"
                  src={`/logos/${company.symbol.toLowerCase()}.svg`}
                  width={20}
                  height={20}
                  className="object-contain rounded-full max-h-[20px]"
                />
                <div className="flex flex-col items-start ml-1">
                  <p className="font-medium">{company.yahooStockV2Summary.price.shortName}</p>
                  <p className="text-muted-foreground">just now</p>
                </div>
              </div>
              <div className="flex flex-col items-end">
                <p className="">${company.price}</p>
                <p className="text-muted-foreground">
                  <Heart className="text-red-600 fill-red-600" width={20} height={20} />
                </p>
              </div>
            </div>
          ))}
        </div>
      }
    </>
  )

}
