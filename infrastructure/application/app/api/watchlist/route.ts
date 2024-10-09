import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";
import { Watchlist_Company, Company } from "@prisma/client";

export async function GET() {
  const { userId } = auth()
  if (!userId)
    return new NextResponse("Unauthorized", { status: 401 });

  const watchlist = await prismadb.watchlist.findFirst({
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

  const watchlistStocks = watchlist.companies.map((item: Watchlist_Company & Company) => item.company);
  console.log("/api/watchlist GET runs")
  return NextResponse.json(watchlistStocks, { status: 200 });
}

export async function PATCH(request: Request) {
  const { isLiked, ticker } = await request.json()
  const { userId } = auth()
  if (!userId)
    return new NextResponse("Unauthorized", { status: 401 });

  const watchlist = await prismadb.watchlist.findFirst({
    where: {
      accountId: userId,
    }
  })
  const company = await prismadb.company.findFirst({
    where: {
      symbol: ticker
    }
  })

  if (isLiked) {
    await prismadb.watchlist_Company.create({
      data: {
        watchlistId: watchlist.id,
        companyId: company.id,
        symbol: ticker
      }
    })
  } else {
    await prismadb.watchlist_Company.delete({
      where: {
        watchlistId_companyId: {
          watchlistId: watchlist.id,
          companyId: company.id
        }
      }
    })
  }

  console.log("watchlist PATCH runs")
  return new NextResponse("PATCH watchlist successful", { status: 200 });
}