"use client"
import {
  DialogContent
} from "@/components/shadcn-ui/dialog"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { z } from "zod"
import toast from "react-hot-toast"
import { Button } from "@/components/shadcn-ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/shadcn-ui/card"
import { Input } from "@/components/shadcn-ui/input"
import { Label } from "@/components/shadcn-ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectGroup,
  SelectLabel
} from "@/components/shadcn-ui/select"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription
} from "@/components/shadcn-ui/form";
import { useOrder } from "@/hooks/use-order";
import { ColorSelector } from "./color-selector";
import { useColor } from '@/hooks/use-color'
const FormSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  cardNumber: z.string().length(19, {
    message: "Card Number must have 19 chracters including space.",
  }).regex(/^[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}$/, {
    message: "Must be in format 'xxxx xxxx xxxx xxxx'"
  }),
  value: z.coerce.number().gte(5000, {
    message: "Value must be from $5,000 to $500,000",
  }).lte(500000, {
    message: "Value must be from $5,000 to $500,000",
  }),
  expiryDate: z.string().regex(/^([0-9][0-9])\/([0-1][0-9])$/, {
    message: "Must be in the format of yy/mm."
  })
})

export const AddCard = () => {
  const { isOpen, setIsOpen } = useOrder()
  const { color } = useColor()
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      name: "",
      cardNumber: "0000 0000 0000 0000",
      value: 250000,
      expiryDate: "",
    },
  })

  function onSubmit(data: z.infer<typeof FormSchema>) {
    addCard(data)
  }

  const queryClient = useQueryClient();
  const { mutate: addCard, isPending } = useMutation({
    mutationFn: (data: z.infer<typeof FormSchema>) => {
      return axios.post("/api/card/add", { data, color })
    },
    onError: (error) => {
      toast.error("Failed adding new card. Duplicate card found")
    },
    onSuccess: () => {
      toast.success("Add Card Successfully")
      form.reset()
      setIsOpen(!isOpen)
      queryClient.invalidateQueries({
        queryKey: ['getCard'],
        exact: true,
        refetchType: 'all'
      })
    }
  })
  return (
    <DialogContent className="w-[396px] pt-[40px] pb-[20px] ">
      <div className="flex justify-center w-full">
        <Card className="w-[350px]">
          <CardHeader>
            <CardTitle>Card Information</CardTitle>
            <CardDescription>Add your card with in one-click.</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-6">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Your card full name" {...field} />
                      </FormControl>

                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="cardNumber"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Card Number</FormLabel>
                      <FormControl>
                        <Input placeholder="Ex. 0123 3456 2345 0123" {...field} />
                      </FormControl>

                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex justify-between gap-6">
                  <FormField
                    control={form.control}
                    name="value"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Value</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <p className="absolute pt-[7px] pl-2">$</p>
                            <Input placeholder="5,000-50,000" {...field} className="pl-5" />
                          </div>
                        </FormControl>

                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="expiryDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Exp Date</FormLabel>
                        <FormControl>
                          <Input placeholder="Ex. 22/09" {...field} />
                        </FormControl>

                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <ColorSelector />
                <div className="flex justify-between mt-12">
                  <Button variant="outline">Cancel</Button>
                  <Button type="submit">{isPending ? "...Submitting" : "Add Card"}</Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </DialogContent>

  )
}

