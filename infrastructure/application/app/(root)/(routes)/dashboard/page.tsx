import prismadb from "@/lib/prismadb";
import { auth } from "@clerk/nextjs";
import {
  AccountContainer,
  BankContainer,
  TableContainer,
  AccordionContainer
} from "./components/index"
import { redirect } from "next/navigation";
import { Company, Watchlist, Watchlist_Company } from "@prisma/client";

const DashboardPage = async () => {
  const { userId } = auth()
  if (!userId) {
    redirect("/")
  }

  // create new user account, skip if already exists
  await prismadb.account.upsert({
    where: {
      id: userId
    },
    update: {},
    create: {
      id: userId,
      accountBalance: 0,
      accountValue: 0,
      portfolio: {
        create: {
          portfolioVal: 0
        }
      },
      watchlist: {
        create: {
          name: "default"
        }
      }
    }
  })

  return (
    <div className="flex flex-1 gap-6 px-6 pt-6">
      <div className="flex flex-col flex-1 h-full ">
        <AccountContainer />
        <TableContainer />
      </div>

      <div className="w-[340px] ">
        <div className="fixed w-[340px] right-6 bottom-4 flex flex-col border rounded-lg border-muted-foreground/30 top-[85px] overflow-auto no-scrollbar">
          <BankContainer />
          <AccordionContainer />
        </div>
      </div>
    </div>
  )
}

export default DashboardPage