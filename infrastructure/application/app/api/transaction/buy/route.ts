import { auth } from "@clerk/nextjs";
import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";

export async function PATCH(request: Request) {
  try {
    const { transaction } = await request.json()
    const { value, symbol } = transaction

    const { userId } = auth()
    if (!userId) {
      return new NextResponse("Unauthorized", { status: 401 });
    }

    const promises = [
      prismadb.portfolio.findFirst({
        where: {
          accountId: userId
        }
      }),
      prismadb.company.findFirst({
        where: {
          symbol
        }
      }),
      prismadb.account.findFirst({
        where: {
          id: userId
        }
      })
    ]
    const [portfolio, company, account] = await Promise.all(promises)

    const portfolioShares = await prismadb.portfolio_Company.findFirst({
      where: {
        portfolioId: portfolio.id,
        companyId: company.id,
      },
      select: {
        shares: true
      }
    })

    const temp = portfolioShares ? portfolioShares.shares : 0

    const allPromies = [
      prismadb.portfolio_Company.upsert({
        where: {
          portfolioId_companyId: {
            portfolioId: portfolio.id,
            companyId: company.id,
          },
        },
        update: {
          shares: temp + value / company.price
        },
        create: {
          portfolioId: portfolio.id,
          companyId: company.id,
          symbol,
          shares: value / company.price
        },
      }),
      prismadb.portfolio.update({
        where: {
          accountId: userId
        },
        data: {
          portfolioVal: portfolio.portfolioVal + value
        }
      }),

      prismadb.account.update({
        where: {
          id: userId
        },
        data: {
          accountBalance: account.accountBalance - value,
          transactions: {
            create: {
              type: `buy ${symbol}`,
              status: 'success',
              amount: value,
            }
          }
        }
      }),

    ]
    await Promise.all(allPromies);


    console.log("api/transaction/buy PATCH runs")
    return new NextResponse("Success", { status: 200 })
  } catch (error) {
    console.log(error);
    return new NextResponse("Internal Error", { status: 500 })
  }
}