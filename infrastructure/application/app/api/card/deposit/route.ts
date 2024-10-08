import { auth } from "@clerk/nextjs";
import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";


export async function PATCH(request: Request) {
  try {
    const { userId } = auth()
    console.log(userId)
    if (!userId)
      return new NextResponse("Unauthorized", { status: 401 });

    const { cardNum, value } = await request.json()

    const foundCard = await prismadb.card.findFirst(
      { where: { cardDigits: cardNum } }
    )
    if (value > foundCard.value) {
      await prismadb.account.update({
        where: {
          id: userId
        },
        data: {
          transactions: {
            create: {
              type: "deposit",
              amount: value,
              status: 'failed'
            }
          }
        }
      })
      return new NextResponse("Insufficient balance", { status: 400 })
    }
    console.log(foundCard)
    await prismadb.card.update({
      where: {
        cardDigits: cardNum
      },
      data: {
        value: foundCard.value - value
      }
    })

    const foundAccount = await prismadb.account.findFirst({ where: { id: userId } })
    await prismadb.account.update({
      where: {
        id: userId
      },
      data: {
        accountBalance: foundAccount.accountBalance + value,
        accountValue: foundAccount.accountValue + value,
        transactions: {
          create: {
            type: `deposit`,
            status: 'success',
            amount: value,
          }
        }
      }
    })
    console.log("card/deposit PATCH runs")
    return new NextResponse("Success", { status: 200 })
  } catch (error) {
    console.log(error);
    return new NextResponse("Internal Error", { status: 500 })
  }
}