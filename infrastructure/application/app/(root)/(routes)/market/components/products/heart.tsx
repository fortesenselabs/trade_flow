"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Check } from "lucide-react";
import { useEffect, useState } from "react";
import { AiOutlineHeart } from "react-icons/ai";
import { IoHeart } from "react-icons/io5";
import { useToast } from "@/components/shadcn-ui/use-toast"
import { useTicker } from "@/hooks/use-ticker";
import { useQuery } from "@tanstack/react-query";
import { Company } from "@prisma/client";
import { Skeleton } from "@/components/shadcn-ui/skeleton";
import { ThreeDots } from "react-loading-icons";


const Heart = () => {
  const { toast } = useToast()
  const { ticker, setIsLiking } = useTicker()

  const { data, isLoading } = useQuery<Company[]>({
    queryKey: ['getWatchlist'],
    queryFn: async () => {
      const response = await axios.get('/api/watchlist')
      return response.data;
    },
    //staleTime: 3600000 // 1 hour in ms only runs once when the component mounts
  })
  const likedSymbols = data?.map((item) => item.symbol) // ['AAPL','AMD']
  const isContained = likedSymbols?.includes(ticker)

  //const [isLiked, setIsLiked] = useState(false)
  const [isDisabled, setIsDisabled] = useState(false)
  const [isLiked, setIsLiked] = useState(isContained)

  useEffect(() => {
    setIsLiked(isContained)
  }, [ticker])

  function handleClicked() {
    setIsLiking(true)
    setIsDisabled(true)
    setIsLiked(!isContained)
    updateWatchlist()

  }
  const queryClient = useQueryClient()
  const { mutate: updateWatchlist, isPending } = useMutation({
    mutationFn: () => {
      return axios.patch("/api/watchlist", {
        isLiked: !isContained,
        ticker: ticker
      })
    },
    onError: (error) => {
      console.log(error)
    },
    onSuccess: () => {
      setIsLiking(false)
      const description = !isContained ? "Added to watchlist" : "Removed from watchlist"
      queryClient.invalidateQueries({
        queryKey: ['getWatchlist'],
        exact: true,
        refetchType: 'all'
      })
      toast({
        className: "shadow-lg gap-2",
        duration: 1500,
        description,
        action: <Check size={24} className="text-white bg-green-500 rounded-full" />,
      })

    }

  })

  if (isPending) return (
    <div className="h-[40px]">
      <ThreeDots
        speed={3}
        width={20}
        height={20}
        fill=""
        className="text-black dark:fill-white"
      />
    </div>
  )

  if (isLoading) return (
    <Skeleton
      className="w-[40px] h-[35px] rounded-lg"
    />
  )

  return (
    <button
      onClick={handleClicked}
      className="transition duration-300 ease-in-out delay-50 hover:-translate-y-1 hover:scale-110"
    >
      {isLiked ?
        <IoHeart
          size={25}
          className="mt-2 text-red-500"
        /> :
        <AiOutlineHeart
          size={25}
          className="mt-2"
        />
      }
    </button>
  )
}

export default Heart