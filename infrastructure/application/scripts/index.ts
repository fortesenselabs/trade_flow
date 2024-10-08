import seedCompanies from "@/scripts/seedCompany";
import seedTickers from "./seedTicker";
import { PrismaClient } from "@prisma/client";
export const db = new PrismaClient();

// Main execution
async function main() {

  try {
    console.log("This main file runs first")
  } catch (error) {
    console.error("Error seeding default stocks", error)
  }
}

main();