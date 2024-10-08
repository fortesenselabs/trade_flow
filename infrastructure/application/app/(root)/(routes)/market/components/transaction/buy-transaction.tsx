"use client"

import * as z from "zod";
import { Label } from "@/components/shadcn-ui/label"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetOverlay,
  SheetTitle,
  SheetTrigger,
} from "@/components/shadcn-ui/sheet"
import { Account, Company } from "@prisma/client"
import axios from "axios";
//import { safeParse } from 'zod'

import * as React from "react"

import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/shadcn-ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/shadcn-ui/input";
import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { useMutation, QueryClient, useQuery, useQueryClient } from "@tanstack/react-query";
import { Separator } from "@/components/shadcn-ui/separator";
interface TransactionProps {
  company: Company,
}

type Transaction = {
  value: number,
  symbol: string
}

export function BuyTransaction({ company }: TransactionProps) {

  const client = useQueryClient();
  const data: Account = client.getQueryData(['getAccount'])
  const symbol = company.symbol;

  const formSchema = z.object({
    prompt: z.coerce.number().int()
      .positive()
      .gte(50, {
        message: "Minimum $50 is required."
      })
      .lte(data.accountBalance, {
        message: `Must be less than or equal to your account balance. Your current account balance: ${data.accountBalance}`,
      })
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      prompt: 50
    }
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      const transaction = {
        value: values.prompt,
        symbol
      }
      updatePortfolio(transaction)
      // clear user input
    } catch (error) {
      console.log("Error submitting the form")
    } finally {
      //router.refresh()
    }
  }

  const queryClient = useQueryClient();
  const { mutate: updatePortfolio, isPending } = useMutation({
    mutationFn: (transaction: Transaction) => {
      return axios.patch("/api/transaction/buy", { transaction })
    },
    onError: (error) => {
      console.log(error)
    },
    onSuccess: () => {
      toast.success("BUY Successful")
      setIsOpen(false)
      form.reset()
      setShareLabel('0')
      queryClient.invalidateQueries({
        queryKey: ['getAccount'],
        exact: true,
        refetchType: 'all'
      })
      queryClient.invalidateQueries({
        queryKey: ['getPortfolio'],
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
    }
  })

  const [isOpen, setIsOpen] = React.useState(false)
  const isLoading = form.formState.isSubmitting;
  const [shareLabel, setShareLabel] = useState("")
  return (
    <Sheet open={isOpen} >
      <SheetTrigger asChild>
        <button
          className={"px-4 py-2 mt-2 text-xs font-medium text-white rounded-lg bg-emerald-600/60"}
          onClick={() => setIsOpen(true)}
        >
          BUY
        </button>
      </SheetTrigger>
      <SheetOverlay
        onClick={() => setIsOpen(false)}
      />
      <SheetContent >
        <SheetHeader>
          <SheetTitle>Buy Stock</SheetTitle>
          <SheetDescription>
            Make stock transactions here
          </SheetDescription>
        </SheetHeader>
        <div className="grid gap-6 py-4">
          <div className="grid items-center grid-cols-4 gap-4">
            <Label htmlFor="name" className="text-right">
              Symbol
            </Label>
            <Label className="col-span-3 pl-4" >
              {symbol}
            </Label>
          </div>
          <div className="grid items-center grid-cols-4 gap-4">
            <Label htmlFor="username" className="text-right">
              Company
            </Label>
            <Label className="col-span-3 pl-4" >
              {company.yahooStockV2Summary.price.shortName}
            </Label>
          </div>

          <div className="grid items-center grid-cols-4 gap-4">
            <Label htmlFor="username" className="text-right">
              Price
            </Label>
            <Label className="col-span-3 pl-4" >
              {company.price}
            </Label>
          </div>

          <Form {...form} >
            <form
              onSubmit={form.handleSubmit(onSubmit)}

              className=""
            >
              <div className="flex gap-4 px-5">
                <p className="text-sm">Amount</p>
                <FormField
                  name="prompt"
                  render={({ field }) => (
                    <FormItem >
                      <FormControl className="px-4 w-[150px]">
                        <Input
                          type="number"
                          disabled={isLoading}
                          placeholder="$50"
                          {...field}
                          onChange={(e) => {
                            field.onChange(e)
                            setShareLabel(`${parseFloat(e.target.value) ? parseFloat(e.target.value) / company.price : 0}`);
                          }}
                        />
                      </FormControl>
                      <FormMessage className="pt-2" />
                    </FormItem>
                  )}
                />
                <p className="mt-2 mr-12 pr-auto">$</p>
              </div>
              {shareLabel !== '0' &&
                <div className="flex justify-end w-full gap-4 pr-[40px] mt-4">

                  <Label className="text-sm text-muted-foreground" >
                    {shareLabel}
                  </Label>
                  <p className="text-sm text-muted-foreground">Shares</p>

                </div>
              }
              <div className="flex justify-end gap-2 pr-2 mt-6">
                <button
                  onClick={() => setIsOpen(false)}
                  type="button"
                  className="px-4 py-2 text-black rounded-lg bg-secondary">
                  Cancel
                </button>

                <button
                  disabled={isPending}
                  type="submit"
                  className="px-6 py-2 text-white bg-black rounded-lg bg-green-600/90"
                >
                  {isPending ? <h1>...Loading</h1> : <h1>BUY</h1>}
                </button>
              </div>
            </form>
          </Form>
        </div>
      </SheetContent>
    </Sheet>
  )
}
