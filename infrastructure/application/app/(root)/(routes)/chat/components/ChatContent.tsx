"use client"

import * as z from "zod";
import { ChatBot, Message } from "@prisma/client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import ChatMessages from "./ChatMessages"
import { Form, FormControl, FormField, FormItem } from "@/components/shadcn-ui/form";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/shadcn-ui/input";
import { formSchema } from "./constants";
import { ArrowRight } from "lucide-react";
import axios from "axios"
import { ChatCompletionRequestMessage } from "openai";

interface ChatContentProps {
  chatBot: ChatBot & {
    messages: Message[]
  },
}

export const ChatContent = ({ chatBot }: ChatContentProps) => {
  // prompt: user's input will be used later
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      prompt: ""
    }
  });

  const isLoading = form.formState.isSubmitting;
  const router = useRouter()

  // array of objects: [{role:.., prompt:...},object2]
  const [messages, setMessages] = useState<ChatCompletionRequestMessage[]>([])

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      // User's current message
      const userMessage: ChatCompletionRequestMessage = {
        role: "user",
        content: values.prompt
      };
      // Append user message
      setMessages((current) => [...current, userMessage])
      const response = await axios.post(`/api/chat`, {
        messages: userMessage
      });

      setMessages((current) => [...current, response.data])

      // clear user input
      form.reset()
    } catch (error) {
      console.log("Error submitting the form")
    } finally {
      router.refresh()
    }
  }


  return (
    <div className="flex flex-col h-full pb-4 border-l border-muted-foreground/30 ">
      <ChatMessages
        isLoading={isLoading}
        messages={messages}
      />
      <Form {...form} >
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex gap-4"
        >
          <FormField
            name="prompt"
            render={({ field }) => (
              <FormItem className="w-full">
                <FormControl className="p-0 m-0">
                  <Input
                    disabled={isLoading}
                    placeholder="Ask any financial questoins"
                    {...field}
                  />
                </FormControl>
              </FormItem>
            )}
          />
          <button className="px-8 rounded-lg bg-muted-foreground/10" type="submit" disabled={isLoading} >
            <ArrowRight />
          </button>
        </form>
      </Form>
    </div>
  )
}