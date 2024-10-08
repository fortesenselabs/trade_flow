import { Company } from "@prisma/client"

interface CompanyDetailsProps {
  foundCompany: Company
}

type financialData = {
  ebitda: { fmt: string },
  totalCash: { fmt: string },
  totalDebt: { fmt: string },
  quickRatio: { fmt: string },
  currentPrice: { fmt: string },
  currentRatio: { fmt: string },
  debtToEquity: { fmt: string },
  freeCashflow: { fmt: string },
  grossMargins: { fmt: string },
  totalRevenue: { fmt: string },
  ebitdaMargins: { fmt: string },
  profitMargins: { fmt: string },
  revenueGrowth: { fmt: string },
  earningsGrowth: { fmt: string },
  returnOnAssets: { fmt: string },
  returnOnEquity: { fmt: string },
  targetLowPrice: { fmt: string },
  revenuePerShare: { fmt: string },
  targetHighPrice: { fmt: string },
  targetMeanPrice: { fmt: string },
  operatingMargins: { fmt: string },
  operatingCashflow: { fmt: string },
  targetMedianPrice: { fmt: string },
  totalCashPerShare: { fmt: string },
  recommendationMean: { fmt: string },
  numberOfAnalystOpinions: { fmt: string },
}

export type insiderHolder = {
  holders: [
    {
      name: string,
      relation: string,
      positionDirect: {
        fmt: string,
      }
    }
  ]
}
const CompanyDetails = ({ foundCompany }: CompanyDetailsProps) => {

  const targetData = foundCompany.yahooStockV2Summary
  const insiderHolders: insiderHolder = targetData.insiderHolders
  const financialData: financialData = targetData.financialData

  const overview = targetData.price;
  const summary = targetData.summaryProfile
  const unixTimestamp = targetData.price.regularMarketTime
  const regularTime = new Date(unixTimestamp * 1000).toUTCString()
  const headers = [
    "Sector",
    "Industry",
    "Fulltime Employees",
    "Website",
    "Address",

    "Summary",

    "Ebitda",
    "TotalCash",
    "TotalDebt",
    "QuickRatio",
    "CurrentPrice",
    "CurrentRatio",
    "DebtToEquity",
    "FreeCashflow",
    "GrossMargin",
    "TotalRevenue",

    "EbitdaMargins",
    "ProfitMargins",
    "RevenueGrowth",
    "EarningsGrowth",
    "ReturnOnAssets",
    "ReturnOnEquity",
    "TargetLowPrice",

    "RevenuePerShare",
    "TargetHighPric",
    "TargetMeanPrice",
    "OperatingMargins",
    "OperatingCashflo",
    "TargetMedianPrice",
    "TotalCashPerShare",
    "RecommendationMean",
    "NumberOfAnalystOpinions",

    "Name",
    "Role",
    "Shares",

    "Company",
    "Zip",
    "City",
    "Phone",
    "State",
    "Country",
    "Industry",
    "Sector",
    "Description",
  ]

  const address = summary.address1 + ", " + summary.city + ", " + summary.state + ", " + summary.zip;
  const data = [
    summary.sector,
    summary.industry,
    summary.fullTimeEmployees,
    summary.website,
    address,

    summary.longBusinessSummary,

    financialData.ebitda.fmt,
    financialData.totalCash.fmt,
    financialData.totalDebt.fmt,
    financialData.quickRatio.fmt,
    financialData.currentPrice.fmt,
    financialData.currentRatio.fmt,
    financialData.debtToEquity.fmt,
    financialData.freeCashflow.fmt,
    financialData.grossMargins.fmt,
    financialData.totalRevenue.fmt,

    financialData.ebitdaMargins.fmt,
    financialData.profitMargins.fmt,
    financialData.revenueGrowth.fmt,
    financialData.earningsGrowth.fmt,
    financialData.returnOnAssets.fmt,
    financialData.returnOnEquity.fmt,
    financialData.targetLowPrice.fmt,
    financialData.revenuePerShare.fmt,
    financialData.targetHighPrice.fmt,
    financialData.targetMeanPrice.fmt,
    financialData.operatingMargins.fmt,
    financialData.operatingCashflow.fmt,
    financialData.targetMedianPrice.fmt,
    financialData.totalCashPerShare.fmt,
    financialData.recommendationMean.fmt,
    financialData.numberOfAnalystOpinions.fmt,

    insiderHolders.holders,

    overview.longName,
    summary.zip,
    summary.city,
    summary.phone,
    summary.state,
    summary.country,
  ]

  return (
    <>
      <div>
        <h1>Updated at {regularTime}</h1>
        <div className="pt-8 pb-2 text-xl font-semibold border-b border-muted-foreground/30">Company Overview</div>
        <div className="px-4 py-6 space-y-2">
          {headers.slice(0, 5).map((item, index) => (
            <div className="flex gap-4">
              <p className="w-[150px]">{item}</p>
              <p className="max-w-[500px] max-h-[200px] overflow-auto font-semibold">{data[index]}</p>
            </div>
          ))}
          <div className="pt-6 leading-6">{data[5]}</div>
        </div>
      </div>
      <div className="pb-8">
        <div className="pt-4 pb-2 text-xl font-semibold border-b border-muted-foreground/30">Financial Data</div>
        <div className="flex justify-between ">
          <div className="w-full px-4 py-6 space-y-2">
            <div className="font-semibold">Valuation</div>
            {headers.slice(6, 15).map((item, index) => (
              <div className="flex justify-between">
                <p className="text-muted-foreground">{item}</p>
                <p className="font-semibold">{data[index + 6]}</p>
              </div>
            ))}
          </div>

          <div className="w-full px-4 py-6 space-y-2">
            <div className="font-semibold">Revenue</div>
            {headers.slice(15, 25).map((item, index) => (
              <div className="flex justify-between">
                <p className="text-muted-foreground">{item}</p>
                <p className="font-semibold ">{data[index + 15]}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="pb-2 text-xl font-semibold border-b border-muted-foreground/30">Top Stakeholders</div>
      <div className="flex flex-wrap justify-between px-4 pb-6">
        {insiderHolders.holders.map((item) => (
          <div className="border border-muted-foreground/30 p-4 w-[30%] space-y-2 mt-6 rounded-lg">
            <p className="font-semibold ">{item.name}</p>
            <div className="flex gap-2">
              <p className="">role</p>
              <p className="font-semibold">{item.relation}</p>
            </div>
            <div className="flex gap-2">
              <p className="">Shares</p>
              {item.positionDirect?.fmt ?
                <p className="font-semibold ">{item.positionDirect?.fmt}</p> :
                <p>No public information available</p>
              }

            </div>
          </div>
        ))}
      </div>
    </>
  )
}

export default CompanyDetails