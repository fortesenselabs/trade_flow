"use client"

import { useAnimation } from "@/hooks/use-animation";
import { cn } from "@/lib/utils";
import { LayoutDashboard } from "lucide-react";
import { useTheme } from "next-themes";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { CiSettings } from "react-icons/ci";
import { IoStorefrontOutline } from "react-icons/io5";
import { TbMessageBolt } from "react-icons/tb";

const Sidebar = () => {
  const { theme } = useTheme()
  const pathName = usePathname()
  const { animatedId, setAnimatedId } = useAnimation()
  const sidebarItems = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      isActive: pathName === "/dashboard"
    },
    {
      name: "Market",
      href: "/market",
      icon: IoStorefrontOutline,
      isActive: pathName === "/market"
    },
    {
      name: "Message",
      href: `/chat`,
      icon: TbMessageBolt,
      isActive: pathName === "/chat"
    },

  ]

  const src = theme === 'light' ? "/landing-page/logo.webp" : "/landing-page/logo2.png"


  return (
    <div className="flex flex-col items-center w-full h-full pt-4 pb-8 border-r border-muted-foreground/30 ">
      <Image
        src={src}
        alt="company logo"
        width={33}
        height={33}
      />

      <div className="space-y-4 text-xs font-medium mt-14">
        {sidebarItems.map((item) => (
          <Link
            prefetch={true}
            key={item.href}
            href={item.href}
            onClick={() => setAnimatedId(2)}
            className={cn("py-2 flex items-center justify-center p-3 group  rounded-lg text-muted-foreground hover:cursor-pointer hover:text-white hover:bg-[#230f61] shadow-md dark:shadow-sm dark:shadow-purple-700",
              item.isActive ? "bg-[#6149cd] text-white shadow-sm shadow-[#19033e]  " : "hover:bg-[#6149cd]/30"
            )}
          >
            <item.icon className="w-5 h-5" />
          </Link>
        ))}
      </div>

      <CiSettings className="w-5 h-5 mt-auto" />
    </div>
  )
}
export default Sidebar;
