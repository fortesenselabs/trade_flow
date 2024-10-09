"use client"
import {
  DialogContent
} from "@/components/shadcn-ui/dialog"
import { QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import { Card as CardModel } from "@prisma/client";
import { TbArrowBarToRight } from "react-icons/tb";
import { useState } from "react";
import { useAccount } from "@/hooks/use-account";
import { useToast } from "@/components/shadcn-ui/use-toast";
import { useColor } from "@/hooks/use-color";

function getFormattedDigits(data: string) {
  const visibleDigits = data.slice(0, 3);
  const lastTwoDigits = data.slice(-4);
  const hiddenDigits = "* **** **** ";
  const formattedCardNumber = visibleDigits + hiddenDigits + lastTwoDigits;
  return formattedCardNumber;
}


export const Deposit = ({ cardLists }: { cardLists: CardModel[] }) => {
  const { color } = useColor()
  const { toast: shadcnToast } = useToast()
  const [shareLabel, setShareLabel] = useState('')
  const { accountVal } = useAccount()
  const { isOpen, setIsOpen } = useOrder()

  const FormSchema = z.object({
    cardNum: z
      .string({
        required_error: "Please select a card.",
      }),
    value: z.coerce.number().gte(500, {
      message: "Value must be from $500 to $50,000",
    }).lte(50000, {
      message: "Value must be from $500 to $50,000",
    }),
  })

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
  })
  function onSubmit(data: z.infer<typeof FormSchema>) {
    deposit(data)
  }

  const queryClient = useQueryClient()
  const { mutate: deposit, isPending } = useMutation({
    mutationFn: (data: z.infer<typeof FormSchema>) => {
      return axios.patch("/api/card/deposit", data)
    },
    onError: (error) => {
      console.log(error)
      shadcnToast({
        variant: "destructive",
        title: "Insufficient card balance.",
      })
      queryClient.invalidateQueries({
        queryKey: ['getTransaction'],
        exact: true,
        refetchType: 'all'
      })
    },
    onSuccess: () => {
      toast.success("Deposit Successfully")
      setIsOpen(!isOpen)
      queryClient.invalidateQueries({
        queryKey: ['getCard'],
        exact: true,
        refetchType: 'all'
      })
      queryClient.invalidateQueries({
        queryKey: ['getAccount2'],
        exact: true,
        refetchType: 'all'
      })
      queryClient.invalidateQueries({
        queryKey: ['getTransaction'],
        exact: true,
        refetchType: 'all'
      })
      form.reset()
    }
  })
  const getCardVal = (data: string) => {
    const foundData = cardLists.find((item) => item.cardDigits === data)
    return foundData ? foundData.value : ""
  }
  const getCardExp = (data: string) => {
    const foundData = cardLists.find((item) => item.cardDigits === data)
    return foundData ? foundData.expiration : ""
  }
  if (!cardLists || cardLists.length === 0) {
    toast.error("Please add card to deposit !")
    return;
  }

  return (
    <DialogContent className="w-[396px] pt-[40px] pb-[20px] h-[550px]">
      <div className="flex justify-center w-full h-full">
        <Card className="w-[350px] ">
          <CardHeader>
            <CardTitle>Deposit Money</CardTitle>
            <CardDescription>Deposit to your account with in one-click.</CardDescription>
          </CardHeader>
          <CardContent className="">

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                <FormField
                  control={form.control}
                  name="cardNum"
                  render={({ field }) => (
                    <FormItem>
                      <Select onValueChange={field.onChange} defaultValue={field.value} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            {field.value ? <SelectValue placeholder="Select Card to deposit" /> : "Select Card to deposit"}
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent className="z-[1000]">
                          <SelectGroup>
                            <SelectLabel>Available cards</SelectLabel>
                            {cardLists.map((item) => (
                              <SelectItem key={item.id} value={item.cardDigits} className="hover:cursor-pointer">
                                <div className="flex py-1 items-center">
                                  {item.cardDigits}
                                  <div className="ml-4 h-[15px] w-[15px] rounded-sm" style={{ backgroundColor: item.color }}></div>
                                </div >
                              </SelectItem>
                            ))}
                          </SelectGroup>
                        </SelectContent>
                      </Select>
                      <FormDescription className="">
                        You can manage your cards in the Card Section
                      </FormDescription>
                      <FormMessage />
                      {field.value &&
                        <>
                          <div className="w-full pt-[20px] text-sm text-muted-foreground">
                            <div className="flex gap-4">
                              <p>Card Value:</p>
                              <p>${getCardVal(field.value)}</p>
                            </div>
                            <div className="flex gap-4">
                              <p>Expiration:</p>
                              <p>{getCardExp(field.value)}</p>
                            </div>
                          </div>

                          <div className="flex gap-6 justify-between">
                            <FormField
                              control={form.control}
                              name="value"

                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Amount</FormLabel>
                                  <FormControl>
                                    <div className="relative">
                                      <p className="absolute pt-[7px] pl-2">$</p>
                                      <Input
                                        type="number"
                                        placeholder="500-5,000"
                                        {...field}
                                        className="pl-5 w-[120px]"
                                        onChange={(e) => {
                                          field.onChange(e)
                                          setShareLabel(`${e.target.value ? parseFloat(e.target.value) + accountVal : accountVal}`);
                                        }}
                                      />
                                    </div>
                                  </FormControl>

                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <TbArrowBarToRight />
                            <div>
                              <div>Account Value</div>
                              <div className="mt-2 text-muted-foreground ">${shareLabel}</div>
                            </div>
                          </div>
                        </>
                      }
                      <div className={`flex justify-between ${field.value ? "pt-[40px]" : "pt-[165px]"}`}>
                        <Button variant="outline">Cancel</Button>
                        <Button type="submit" >{isPending ? "...Depositing" : "Deposit"}</Button>
                      </div>
                    </FormItem>
                  )}
                />
              </form>
            </Form>
          </CardContent>

        </Card>

      </div>
    </DialogContent>
  )
}

