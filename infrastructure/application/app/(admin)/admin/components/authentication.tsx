"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { useQueryClient, useMutation } from "@tanstack/react-query"
import { Button } from "@/components/shadcn-ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/shadcn-ui/form"
import { Input } from "@/components/shadcn-ui/input"
import axios from "axios"
import { useToast } from "@/components/shadcn-ui/use-toast"
import toast from "react-hot-toast"
import { useRouter } from "next/navigation"

const formSchema = z.object({
  username: z.string().min(2, {
    message: "Username must be at least 2 characters.",
  }),
})

interface AuthenticationProps {
  isSuccess: boolean,
  setIsSuccess: (isSuccess: boolean) => void
}

export function Authentication({ isSuccess, setIsSuccess }: AuthenticationProps) {
  const { toast: shadcnToast } = useToast()
  const router = useRouter()
  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      authenticate(values)
      // clear user input
    } catch (error) {
      console.log("Error submitting the form")
    } finally {
      //router.refresh()
    }
  }

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
    },
  })

  const queryClient = useQueryClient();
  const { mutate: authenticate, isPending } = useMutation({
    mutationFn: (values: z.infer<typeof formSchema>) => {
      return axios.post("/api/admin/authenticate", { values })
    },
    onError: (error) => {
      shadcnToast({
        variant: "destructive",
        title: "Wrong key.",
      })
      console.log(error)
    },
    onSuccess: () => {
      toast.success("Login Successfully")
      setIsSuccess(!isSuccess);
    }
  })


  return (
    <div className="flex items-center justify-center h-screen">

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <FormField
            control={form.control}
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Admin Code</FormLabel>
                <FormControl>
                  <Input placeholder="Enter your admin code" {...field} />
                </FormControl>
                <FormDescription>
                  This is your public display name.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit">Submit</Button>
        </form>
      </Form>
    </div>
  )
}
