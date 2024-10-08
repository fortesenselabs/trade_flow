import { cn } from "@/lib/utils";
import Image from "next/image";
import { ChatCompletionRequestMessageRoleEnum } from "openai";
import { BeatLoader } from "react-spinners"
import { UserAvatar } from "./UserAvatar";
import BotAvatar from "./BotAvatar";

export interface ChatMessageProps {
  role: ChatCompletionRequestMessageRoleEnum;
  content?: string;
  isLoading?: boolean;
  src?: string
}

const ChatMessage = ({
  role,
  content,
  isLoading,
  src
}: ChatMessageProps) => {
  return (
    <div className={cn("flex items-start gap-x-3 py-4 w-full",
      role === "user" && "justify-end")}>
      {role !== "user" &&
        <BotAvatar/>
      }
      <div className="max-w-sm px-4 py-2 rounded-md bg-primary/10">
        {isLoading
          ? <BeatLoader
            size={5}
            color="black" />
          : content}
      </div>
      {role === "user" &&
        <UserAvatar />
      }
    </div>
  )
}

export default ChatMessage