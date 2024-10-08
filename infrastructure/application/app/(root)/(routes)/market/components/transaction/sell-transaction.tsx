"use client"

import { Label } from "@/components/shadcn-ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetOverlay,
  SheetTitle,
  SheetTrigger,
} from "@/components/shadcn-ui/sheet";
import { Account, Company, Portfolio, Portfolio_Company } from "@prisma/client";
import axios from "axios";
import { useRouter } from "next/navigation";
import * as z from "zod";
//import { safeParse } from 'zod'

import * as React from "react";

import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/shadcn-ui/form";
import { Input } from "@/components/shadcn-ui/input";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
interface TransactionProps {
  company: Company,
}

type Transaction = {
  value: number,
  symbol: string
}

export function SellTransaction({ company }: TransactionProps) {

  const client = useQueryClient();
  const data: Account & Portfolio & Portfolio_Company[] = client.getQueryData(['getAccount'])
  const symbol = company.symbol;
  const portfolioStocks: Portfolio_Company[] = data.portfolio.companies

  const foundStock = portfolioStocks.filter((item) => item.symbol.includes(company.symbol))
  const foundStockPrice = foundStock.length === 0 ? 0 : foundStock[0].shares * company.price

  const shareAmount = foundStock.length === 0 ? 0 : foundStock[0].shares
  const price = portfolioStocks.length === 0 ? 0 : foundStockPrice

  const formSchema = z.object({
    prompt: z.coerce.number().int()
      .positive()
      .gt(0, {
        message: "Must be greater than $0.00"
      })
      .lte(price, {
        message: `You currently have ${shareAmount} shares. Not enough ${company.symbol} stocks`
      })
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      prompt: 0
    }
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      const transaction = {
        value: values.prompt,
        symbol
      }
      updatePortfolio(transaction)
    } catch (error) {
      console.log("Error submitting the form")
    }
  }

  const queryClient = useQueryClient();
  const { mutate: updatePortfolio, isPending } = useMutation({
    mutationFn: (transaction: Transaction) => {
      return axios.patch("/api/transaction/sell", { transaction })
    },
    onError: (error) => {
      console.log(error)
    },
    onSuccess: () => {
      toast.success("SELL Successful")
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
  const router = useRouter()

  const [shareLabel, setShareLabel] = useState("")
  return (
    <Sheet open={isOpen} >
      <SheetTrigger asChild>
        <button
          className={"px-4 py-2 mt-2 text-xs font-medium text-white rounded-lg bg-red-600/60"}
          onClick={() => setIsOpen(true)}
        >
          SELL
        </button>
      </SheetTrigger>
      <SheetOverlay
        onClick={() => setIsOpen(false)}
      />
      <SheetContent >
        <SheetHeader>
          <SheetTitle>Sell Stock</SheetTitle>
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
                  className={`bg-red-600/90 px-6 py-2 text-white bg-black rounded-lg`}>
                  {isPending ? <h1>...Loading</h1> : <h1>SELL</h1>}
                </button>
              </div>
            </form>
          </Form>
        </div>
      </SheetContent>
    </Sheet>
  )
}
