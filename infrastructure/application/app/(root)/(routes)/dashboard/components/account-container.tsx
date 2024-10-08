"use client"

import { dashboardHeaders } from '@/constants'
import { AccountCard } from './index'
import { QueryClient, useQueryClient } from '@tanstack/react-query'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { Skeleton } from '@/components/shadcn-ui/skeleton'
import { useAccount } from '@/hooks/use-account'
import { useEffect } from 'react'

const AccountContainer = () => {
  const { accountVal, setAccountVal } = useAccount()
  const { data, isLoading } = useQuery({
    queryKey: ['getAccount2'],
    queryFn: async () => {
      const response = await axios.get('/api/account')
      return response.data;
    },
  })
  useEffect(() => {
    if (!isLoading) {
      setAccountVal(data.accountBalance)
    }
  }, [data])
  if (isLoading) {
    return <div className='flex justify-between'>
      {dashboardHeaders.map((item, index) =>
        <Skeleton className='w-[250px] h-[200px] rounded-lg' />
      )}
    </div>
  }

  const total = data.accountBalance + data.portfolio.portfolioVal
  const dataArr = [
    total,
    data.accountBalance,
    data.portfolio.portfolioVal
  ]

  return (
    <div className="flex justify-between">
      {dashboardHeaders.map((item, index) =>
        <AccountCard
          key={item.title}
          title={item.title}
          value={dataArr[index]}
          percentChange={item.percentChange}
          index={index}
        />
      )}
    </div>
  )
}

export default AccountContainer