import { auth } from "@clerk/nextjs";
import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";

export async function GET() {
  try {
    const { userId } = auth()
    if (!userId) {
      return new NextResponse("Unauthorized", { status: 401 })
    }
    const account = await prismadb.account.findFirst({
      where: {
        id: userId
      },
      include: {
        portfolio: {
          include: {
            companies: true

          }
        }
      }
    }
    )
    //console.log(account);
    console.log("account GET route runs")
    return NextResponse.json(account, { status: 200 })
  } catch (error) {
    console.log(error)
    return new NextResponse("Internal Error", { status: 500 })
  }
}

