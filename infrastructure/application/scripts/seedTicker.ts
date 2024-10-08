import axios from "axios"
import { db } from "@/scripts/index";


const popularTickers = ['AAPL', 'ABNB', 'AMZN', 'BA', 'CISCO', 'COLA', 'EBAY', 'GOOGL', 'IBM', 'JD', 'MA', 'META', 'MSFT', 'NIKE', 'NVDA', 'TESLA'
]

// Fetch trending tickers
async function fetchTrendingTickers() {
  const options = {
    method: 'GET',
    url: 'https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/get-trending-tickers',
    params: { region: 'US' },
    headers: {
      'X-RapidAPI-Key': '8f54d4c5c3msh2a085748e236832p1f8830jsndd3103bf567c',
      'X-RapidAPI-Host': 'apidojo-yahoo-finance-v1.p.rapidapi.com'
    }
  };

  try {
    const response = await axios.request(options);
    return response.data.finance.result[0].quotes;
  } catch (error) {
    console.error(error);
  }
}

// Fetch top active tickers
async function fetchActiveTickers() {
  const options = {
    method: 'GET',
    url: 'https://apidojo-yahoo-finance-v1.p.rapidapi.com/screeners/get-symbols-by-predefined',
    params: {
      scrIds: 'MOST_WATCHED_TICKERS',
      start: '0',
      count: '200'
    },
    headers: {
      'X-RapidAPI-Key': '8f54d4c5c3msh2a085748e236832p1f8830jsndd3103bf567c',
      'X-RapidAPI-Host': 'apidojo-yahoo-finance-v1.p.rapidapi.com'
    }
  };

  try {
    const response = await axios.request(options);
    return response.data.finance.result[0].quotes
  } catch (error) {
    console.error(error);
  }
}

// Fetch all tickers excluding those containing '.'
async function fetchAllTickers() {
  const options = {
    method: 'GET',
    url: 'https://real-time-quotes1.p.rapidapi.com/api/v1/symbol/stock',
    params: {
      includeNames: 'false'
    },
    headers: {
      'X-RapidAPI-Key': '8f54d4c5c3msh2a085748e236832p1f8830jsndd3103bf567c',
      'X-RapidAPI-Host': 'real-time-quotes1.p.rapidapi.com'
    }
  };

  try {
    const response = await axios.request(options);
    return response.data;
  } catch (error) {
    console.error(error);
  }
}

async function seedTickers() {
  try {
    await db.ticker.deleteMany();
    const promises = [];
    for (let i = 0; i < popularTickers.length; i++) {
      promises.push(db.ticker.upsert({
        where: {
          symbol: popularTickers[i]
        },
        update: {},
        create: {
          symbol: popularTickers[i],
        }
      }))
    }
    await Promise.all(promises)


    console.log("sucessfully seeding ticker")
  } catch (error) {
    console.error("Error seeding tickers", error)
  } finally {
    await db.$disconnect
  }
}

seedTickers()

export default seedTickers
// run file: npx tsx scripts/seedTicker.ts
