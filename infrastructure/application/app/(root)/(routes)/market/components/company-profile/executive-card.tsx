import Image from "next/image";

interface ExecutiveProps {
  employee: {
    name: string,
    role: string,
    avatarImg: string,
    shares: string
  }
}

const ExecutiveCard = ({ employee }: ExecutiveProps) => {
  const { name, role, avatarImg, shares } = employee;
  return (
    <div className="w-[110px] h-[130px] relative flex flex-col items-center justify-center text-xs shadow-lg dark:shadow-red-600 rounded-lg dark:shadow-sm">
      <Image
        alt="avatar"
        src={avatarImg}
        width={30}
        height={30}
        className="absolute -top-[15px] rounded-full"
      />
      <p className="text-[10px] mb-2 mt-2 text-center">{name}</p>
      <p className="text-center">{role}</p>
      <p className="pt-4">{shares}</p>
    </div>
  )
}

export default ExecutiveCard