import { db } from "."

async function seedMessage() {
  await db.chatBot.create({
    data: {
      messages: {
        create: {
          content: "Hey there! I'm a chatbot, how can i help you",
          role: "system"
        }
      }
    }
  })
}
seedMessage()

// npx tsx scripts/seedMessage.ts