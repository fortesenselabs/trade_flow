import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";
import { Portfolio_Company, Watchlist_Company, Company } from "@prisma/client";

export async function POST(request: Request) {
  const { userId } = auth()
  if (!userId)
    return new NextResponse("Unauthorized", { status: 401 });
  const { data, color } = await request.json()
  const { name, cardNumber, value, expiryDate } = data
  await prismadb.card.create({
    data: {
      holderName: name,
      value: value,
      expiration: expiryDate,
      cardDigits: cardNumber,
      type: "VISA",
      accountId: userId,
      color
    },
  })


  console.log("card/add POST runs")
  return NextResponse.json("", { status: 200 });
}