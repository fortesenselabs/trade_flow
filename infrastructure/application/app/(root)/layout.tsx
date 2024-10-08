import { Navbar } from "@/components/app/navbar"
import Sidebar from "@/components/app/sidebar"

const RootLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="h-screen ">
      <aside className="w-[75px] h-full fixed z-[101]">
        <Sidebar />
      </aside>
      <div className="fixed w-full pl-[75px] z-[100] ">
        <Navbar />
      </div>

      <main className="ml-[75px] pt-[60px] h-full flex flex-col">
        {children}
      </main>
    </div>
  )
}

export default RootLayout