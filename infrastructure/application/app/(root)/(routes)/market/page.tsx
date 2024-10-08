import prismadb from "@/lib/prismadb"
import MarketContainer from "./components/market-container"
import { auth } from "@clerk/nextjs"
import { redirect } from "next/navigation"

interface MarketProps {
  searchParams: {
    symbol: string
  }
}

const Market = async () => {
  const { userId } = auth()
  if (!userId) {
    redirect("/")
  }
  // fetching
  const companies = await prismadb.company.findMany()

  return (
    <MarketContainer
      companies={companies}
    />
  )
}

export default Market