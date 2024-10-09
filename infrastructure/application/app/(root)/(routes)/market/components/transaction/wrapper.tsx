import { Company } from "@prisma/client"
import { BuyTransaction } from "./buy-transaction"
import { SellTransaction } from "./sell-transaction"
import { useQuery } from "@tanstack/react-query"
import axios from "axios"
import { useTicker } from "@/hooks/use-ticker"
import { Skeleton } from "@/components/shadcn-ui/skeleton"
interface WrapperInterface {
  company: Company
}

const Wrapper = ({
  company
}: WrapperInterface) => {
  const { ticker } = useTicker()
  const { isLoading } = useQuery({
    queryKey: ['getAccount'],
    queryFn: async () => {
      const response = await axios.get('/api/account')
      return response.data;
    },
  })
  if (isLoading) return (
    <div className="flex gap-1">
      <Skeleton className="w-[60px] h-[40px] rounded-lg" />
      <Skeleton className="w-[60px] h-[40px] rounded-lg" />
    </div>
  )
  return (
    <>
      <div className="flex gap-1">
        <SellTransaction company={company} />
        <BuyTransaction company={company} />
      </div>
    </>
  )
}

export default Wrapper