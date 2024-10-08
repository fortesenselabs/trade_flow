import { useUser } from "@clerk/nextjs"
import { redirect } from "next/navigation"

export const Greetings = () => {
  const user = useUser()
  if (!user) {
    redirect('/')
  }
  const firstName = user.user?.firstName
  const lastName = user.user?.lastName
  console.log(user)
  return (
    <div className="mb-6">
      <p className="text-2xl font-semibold">Welcome Back, {firstName} {lastName}</p>
      <p className="text-muted-foreground">Here is the list of your recent transactions</p>
    </div>
  )
}