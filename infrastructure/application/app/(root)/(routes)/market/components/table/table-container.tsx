
import { DataTable } from "./data-table"
import { columns, CompanyDef } from "./columns"
import { Company } from "@prisma/client"

interface TableContainerProps {
  companies: Company[],
}

const TableContainer = ({ companies }: TableContainerProps) => {
  const data = companies.map((item) => (
    {
      symbol: item.symbol,
      sector: item.yahooStockV2Summary.summaryProfile.sector,
      trend: item.yahooStockV2Summary.financialData.recommendationKey,
      price: item.price,
      percentChg: item.yahooStockV2Summary.price.regularMarketChange.fmt
    }
  ))

  return (
    <DataTable columns={columns} data={data} />
  )
}

export default TableContainer