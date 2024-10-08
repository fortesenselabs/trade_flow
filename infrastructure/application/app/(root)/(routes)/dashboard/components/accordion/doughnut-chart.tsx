"use client"

import 'chart.js/auto';
import { Company, Portfolio } from '@prisma/client';
import axios from 'axios';
import Image from 'next/image';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query'
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton';
import { ThreeDots } from 'react-loading-icons'
import { Doughnut } from 'react-chartjs-2';
import { Portfolio_Company } from '@prisma/client';
export function DoughnutChart() {
  const { data: queryData, isLoading } = useQuery<Portfolio_Company & Company[]>({
    queryKey: ['getPortfolio'],
    queryFn: async () => {
      const response = await axios.get('/api/portfolio')
      return response.data;
    },
    staleTime: 3600000 // 1 hour in ms
  })
  if (isLoading || !queryData) {
    return (
      <div className='flex items-center justify-center h-[30px] text-muted-foreground'>
        ...Loading
      </div>
    );
  }

  const arrSymbols = queryData.companies.map((item: Company) => item.symbol);
  const arrData: number[] = queryData.companies.map((item: Portfolio_Company) => {
    return item.shares * item.company.price
  })
  const total = arrData.length === 0 ? 0 : arrData.length === 1 ? 1 : arrData.reduce((a, b) => a + b)
  const arrPercent = total === 0 ? [] : total === 1 ? [100] : arrData.map((item) => Math.max(item / total * 100, 2))

  const bgColors = ['#035380', '#00803d', '#803335', '#17807b', '#144f80']
  //const arrValues = queryData.map((item)=>item.)
  const options = {}
  const data =
  {
    labels: arrSymbols,
    datasets: [{
      label: '% of Total',
      data: arrPercent,
      borderWidth: 4,
      hoverOffset: 15,
      hoverBorderColor: '#6149cd',
    }]
  };


  return (
    <div className='relative flex items-center justify-center h-[40vh]'>
      <div className='absolute flex flex-col items-center -z-50'>
        <p className='text-lg font-medium'>{arrSymbols.length}</p>
        <p className='text-xs text-muted-foreground'>Stocks</p>
      </div>
      <div className='w-[180px] h-[180px]'>
        <Doughnut
          data={data}
          options={
            {
              color: 'black',
              layout: {
                padding: 10
              },
              plugins: {
                legend: {
                  display: false
                },

              },
              maintainAspectRatio: false,
              cutout: '65%',

            }
          }
        />
      </div>
    </div>
  )
}

