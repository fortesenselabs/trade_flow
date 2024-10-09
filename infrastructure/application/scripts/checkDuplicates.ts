import { db } from "@/scripts/index"
import { Company } from "@prisma/client";

const compareArrays = (arr1: string[], arr2: string[]): boolean => {
  if (arr1.length !== arr2.length) {
    console.log("not same length")
    return false;

  }
  return arr1.every((value) => arr2.includes(value));

};

const compareArrays2 = (arr1: string[], arr2: string[]): number[] => {
  if (arr1.length !== arr2.length) {
    console.log("not same length")
    return [0];

  }
  const result = []
  for (let i = 0; i < arr1.length; i++) {
    if (arr1[i] !== arr2[i]) {
      result.push(i)
    }
  }
  return result;

};
export async function checkDuplicate() {
  const companies: Company[] = await db.company.findMany()
  const symbols = companies.map((item: Company) => item.symbol)
  const summary = companies.map((item) => item.yahooStockV2Summary.symbol)

  console.log(compareArrays(symbols, summary))
  console.log(compareArrays2(symbols, summary))
}

checkDuplicate()
// npx tsx scripts/checkDuplicates.ts