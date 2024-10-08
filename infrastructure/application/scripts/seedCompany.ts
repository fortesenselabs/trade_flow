import axios from "axios"
import { db } from "@/scripts/index"
import { Company } from "@prisma/client";

// Get detail data for individual stock
async function fetchStockV2Summary(symbol: string) {
  const options = {
    method: 'GET',
    url: 'https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary',
    params: {
      symbol: symbol,
      region: 'US'
    },
    headers: {
      'X-RapidAPI-Key': process.env.YAHOO_FINANCE_STOCK_SUMMARY,
      'X-RapidAPI-Host': 'apidojo-yahoo-finance-v1.p.rapidapi.com'
    }
  };

  try {
    const response = await axios.request(options);
    return response.data
  } catch (error) {
    console.error(error);
  }
}

// Fetches stock summaries for multiple symbols
async function getStockV2Summary(symbols: string[]) {
  const result = []
  for (let i = 0; i < symbols.length; i++) {
    const summary = await fetchStockV2Summary(symbols[i]);
    result.push(summary)
  }
  return result;
}

// Seeds company data into the database
async function seedCompanies() {
  try {
    await db.company.deleteMany()
    const symbolList = await db.ticker.findMany({
      select: {
        symbol: true
      }
    })
    const companies: Company[] = await db.company.findMany()
    const existingSymbols = companies.map((item) => item.symbol)
    const allSymbols: string[] = symbolList.map((item: { symbol: string }) => item.symbol)
    const symbols = allSymbols.filter((symbol) => existingSymbols.indexOf(symbol) === -1);

    const start = 0;
    const end = symbols.length < 10 ? symbols.length : 40;
    const stockV2Summary = await getStockV2Summary(symbols.slice(start, end))

    console.log("total: " + symbols.length);
    console.log("V2GetSummary actual: " + stockV2Summary.length)

    await Promise.all(symbols.slice(start, end).map(async (symbol: string, index: number) => (
      db.company.upsert({
        where: {
          symbol
        },
        update: {},
        create: {
          symbol,
          price: stockV2Summary[index].price.regularMarketPrice.raw,
          yahooStockV2Summary: stockV2Summary[index],
        }
      })
    )))

    console.log("seeding company data successfully");
  } catch (error) {
    console.log("error seeding company data", error)
  }
}

seedCompanies()

export default seedCompanies
// npx tsx scripts/seedCompany.ts