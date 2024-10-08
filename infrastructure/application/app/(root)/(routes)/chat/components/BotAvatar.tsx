import Image from "next/image"
const BotAvatar = () => {

  return (
    <Image
      src="/logos/dynamitetrade.png"
      alt="bot-image"
      width={30}
      height={30}
      className="object-contain bg-purple-700 rounded-full"
    />
  )
}

export default BotAvatar