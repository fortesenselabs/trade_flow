import { useQuery } from "@tanstack/react-query"
import axios from "axios"
import { CardContent } from "./card-content"
import { Card } from "@prisma/client"
import 'react-loading-skeleton/dist/skeleton.css'
import { Skeleton } from "@/components/shadcn-ui/skeleton"

const contents = [
  {
    className: "p-2",
    order: "1",
  },
  {
    className: "px-2 absolute -z-[2] w-full top-2 -right-2 opacity-80",
    order: "2"
  }
]
export const Wrapper = () => {

  const { data, isLoading } = useQuery<Card[]>({
    queryKey: ['getCard'],
    queryFn: async () => {
      const result = await axios.get("/api/card")
      return result.data;
    }
  })
  if (isLoading) return (
    <Skeleton
      className="h-[150px] mx-4"
    />
  )
  return (
    <>
      {!data || data.length === 0 ?
        <div className="h-[164px] flex items-center justify-center text-muted-foreground text-sm">
          No cards added.
        </div> :
        <div className="relative py-2 ">
          {data.slice(0, 2).map((item, index) => (
            <CardContent key={index} className={contents[index].className} order={contents[index].className} cardData={item} />
          ))}

        </div>
      }
    </>
  )
}