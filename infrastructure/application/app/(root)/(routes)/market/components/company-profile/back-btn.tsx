import { useAnimation } from "@/hooks/use-animation";
import { MoveLeft } from "lucide-react";
import { cn } from "@/lib/utils";

const BackBtn = () => {
  const { animatedId, setAnimatedId } = useAnimation()

  return (
    <button
      onClick={() => {
        setAnimatedId(2)
      }}
      className={cn("flex gap-1 px-2 py-1 items-center justify-center shadow-md rounded-md h-[30px] hover:text-white hover:bg-black dark:shadow-green-600")}
    >
      <MoveLeft
        size={16}
      />
      <p className="text-xs ">Market</p>
    </button>
  )
}

export default BackBtn