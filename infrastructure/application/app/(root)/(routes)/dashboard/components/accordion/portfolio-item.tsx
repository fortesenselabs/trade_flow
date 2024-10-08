"use client"

import { Company, Portfolio } from '@prisma/client';
import axios from 'axios';
import Image from 'next/image';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query'
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import { ThreeDots } from 'react-loading-icons'
import { Portfolio_Company } from '@prisma/client';

export const PortfolioItem = () => {

  const { data: queryData, isLoading } = useQuery<Portfolio_Company & Company[]>({
    queryKey: ['getPortfolio'],
    queryFn: async () => {
      const response = await axios.get('/api/portfolio')
      return response.data;
    },
  })

  if (isLoading || !queryData) {
    return (
      <div className='flex items-center justify-center h-[30px] text-muted-foreground'>
        ...Loading
      </div>
    );
  }
  //const data: Company[] = queryData.companies.map((item: Portfolio_Company & Company) => item.company);
  const data2 = queryData.companies
  console.log(data2)
  return (
    <>
      {
        !data2 || data2.length === 0 ?
          <div className='h-[30px] flex justify-center items-center text-muted-foreground text-sm'>
            No stocks added.
          </div> :
          <div className="flex flex-col gap-3 mt-4 ">
            {data2.map((company: Portfolio_Company & Company) => (
              <button
                key={company.id}
                className="flex justify-between px-4 py-2 text-xs rounded-md shadow-md "
              >
                <div className="flex items-center gap-2 w-[150px]">
                  <Image
                    alt="stock img"
                    src={`/logos/${company.symbol.toLowerCase()}.svg`}
                    width={22}
                    height={22}
                    className="object-contain rounded-full p-[2px] dark:bg-slate-200"
                  />
                  <div className="flex flex-col items-start ml-1">
                    <p className="font-medium">{company.symbol}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  <p className="">${(company.shares * company.company.price).toFixed(2)}</p>
                  <p className="text-muted-foreground">{company.shares.toFixed(8) + " shares"}</p>
                </div>
              </button>
            ))}
          </div>
      }
    </>
  )
}

