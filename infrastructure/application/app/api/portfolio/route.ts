import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";
import { Portfolio_Company, Watchlist_Company, Company } from "@prisma/client";



export async function GET() {
  const { userId } = auth()
  if (!userId)
    return new NextResponse("Unauthorized", { status: 401 });

  const portfolio = await prismadb.portfolio.findFirst({
    where: {
      accountId: userId
    },
    include: {
      companies: {
        include: {
          company: true
        }
      }
    }
  })
  console.log(portfolio);
  const portfolioStocks = portfolio.companies.map((item: Portfolio_Company & Company) => item.company);
  console.log("portfolio GET route runs")
  return NextResponse.json(portfolio, { status: 200 });

}