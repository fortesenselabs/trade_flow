import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";

export async function GET() {
  const { userId } = auth()
  if (!userId)
    return new NextResponse("Unauthorized", { status: 401 });

  const result = await prismadb.account.findFirst({
    where: {
      id: userId
    },
    include: {
      cards: true
    }
  })

  console.log("card GET route runs")
  return NextResponse.json(result.cards, { status: 200 });
}