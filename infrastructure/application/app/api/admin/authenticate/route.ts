import { NextResponse } from "next/server";
import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";

export async function POST(request: Request) {
  const body = await request.json();
  const { values } = body;
  console.log(values)
  if (values.username !== '12345')
    return new Response("InCorrect Password!", { status: 400 });

  return new NextResponse("Correct key", { status: 200 });
}