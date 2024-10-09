import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";

export async function GET() {
  try {
    const result = []
    const accounts = await prismadb.account.findMany({
      include: {
        portfolio: {
          include: {
            companies: true
          }
        },
        watchlist: {
          include: {
            companies: true
          }
        },
        cards: true,
        transactions: true
      }
    });

    console.log(accounts)
    return NextResponse.json(accounts, { status: 200 });
  } catch (error) {
    console.log(error)
    return new NextResponse("Internal error", { status: 500 });
  }
}