import prismadb from "@/lib/prismadb"
import { Account } from "@prisma/client"
import { useQuery } from "@tanstack/react-query"
import axios from "axios"
import Link from "next/link"

export const Contents = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['getAllData'],
    queryFn: async () => {
      const response = await axios.get("/api/admin")
      return response.data
    }
  })
  console.log(data)
  if (isLoading) {
    return <div>loading...</div>
  }
  return (
    <div className="relative px-32 pt-8">
      <Link
        href="/"
        className="absolute px-4 py-2 text-sm shadow-xl right-32"
      >
        Home
      </Link>
      <p className="pb-8 text-2xl font-medium">Number of active users: {data.length}</p>
      <div>
        <p className="pb-2 text-xl font-medium border-b border-muted-foreground/30">Users</p>
        <div className="flex flex-wrap justify-between">
          {data.map((item: Account) => (
            <div key={item.id} className="w-[500px] h-[150px] shadow-md flex flex-col justify-between p-6 mt-8 text-muted-foreground">
              <div className="flex justify-between">
                <p>UserId</p>
                <p className="font-medium text-black">{item.id}</p>
              </div>
              <div className="flex justify-between">
                <p>Account balance</p>
                <p className="font-medium text-black">${item.accountBalance}</p>
              </div>
              <div className="flex justify-between">
                <p>Account value</p>
                <p className="font-medium text-black">${item.accountValue}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {data.map((item: Account, index: number) => (
        <div key={item.id} className="mt-12">
          <p className="pb-2 text-xl font-medium border-b border-muted-foreground/30">User {item.id}</p>
          <p>Portfolio: {item.portfolio.companies.length} stocks</p>
          <div className="flex flex-wrap gap-8">
            {item.portfolio.companies.map((item2: Account) => (
              <div key={item.id} className="flex flex-col justify-between p-6 mt-8 w-[300px] shadow-md text-muted-foreground">
                <div className="flex justify-between">
                  <p>Symbol</p>
                  <p className="font-medium text-black">{item2.symbol}</p>
                </div>
                <div className="flex justify-between">
                  <p>Price</p>
                  <p className="font-medium text-black">${item2.price}</p>
                </div>

              </div>
            ))}
          </div>
        </div>
      ))}


    </div>
  )
}