"use client"
import { columns } from "./table/columns"
import { DataTable } from "./index"
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Skeleton } from "@/components/shadcn-ui/skeleton";
import { Transaction } from "@prisma/client";
import { Greetings } from "./table/greetings";


const TableContainer = () => {
  const { data: transactionData, isLoading } = useQuery<Transaction[]>({
    queryKey: ['getTransaction'],
    queryFn: async () => {
      const response = await axios.get("/api/transaction")
      return response.data;
    }
  })
  if (isLoading || !transactionData) return (
    <div className="flex-1 mt-8 border rounded-t-lg border-muted-foreground/30">
      <Skeleton
        className="w-full h-full"
      />
    </div>
  );
  return (
    <div className="flex-1 mt-8 border rounded-t-lg border-muted-foreground/30 p-6 h-full">
      <Greetings />
      <DataTable
        columns={columns}
        data={transactionData}
      />
    </div>

  )
}

export default TableContainer