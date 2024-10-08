import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";

export async function POST(request: Request) {
  const { userId } = auth()
  if (!userId)
    return new NextResponse("Unauthorized", { status: 401 });
  const body = await request.json()
  console.log(body)
  await prismadb.card.delete({
    where: {
      cardDigits: body.cardNum
    }
  })


  console.log("card/remove POST route runs")
  return new NextResponse("Delete card successfully", { status: 200 });
}