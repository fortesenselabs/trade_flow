import { ChatContent } from "./components/ChatContent"
import prismadb from "@/lib/prismadb"
import SideContent from "./components/SideContent"

/**
 * This components renders the chat bot page.
 */
const MessengerPage = async () => {
  const chatBot = await prismadb.chatBot.findFirst({
    include: {
      messages: true
    }
  })
  return (
    <div className="flex flex-1 w-full">
      <div className="w-[25%]">
        <SideContent />
      </div>
      <div className="flex-1">
        <ChatContent chatBot={chatBot} />
      </div>
    </div>
  )
}

export default MessengerPage