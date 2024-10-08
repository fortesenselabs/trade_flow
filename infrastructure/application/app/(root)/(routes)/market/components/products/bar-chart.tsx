"use client"

import 'chart.js/auto';
import { Company } from "@prisma/client"
import { Bar } from "react-chartjs-2"
import Utils from "react-chartjs-2"
interface BarChartProps {
  company: Company
}
type chartData = {
  date: string,
  revenue: {
    raw: Number
  },
  earnings: {
    raw: Number
  }
}
export const BarChart = ({ company }: BarChartProps) => {
  const DATA_COUNT = 7;
  //const NUMBER_CFG = { count: DATA_COUNT, min: -100, max: 100 };
  const values: chartData[] = company.yahooStockV2Summary.earnings.financialsChart.quarterly
  const labels = values.map((value) => {
    const firstTwo = value.date.slice(0, 2)
    const last = value.date.slice(-4)
    return firstTwo + ' ' + last
  })
  const revenueData = values.map((value) => value.revenue.raw)
  const earningsData = values.map((value) => value.earnings.raw)
  return (
    <div className="w-full mt-auto ">
      <Bar
        data={
          {
            labels: labels,
            datasets: [
              {
                label: 'Earnings',
                data: earningsData,
                borderColor: "#e1575f",
                backgroundColor: "rgba(9,162,143)"
              },
              {
                label: 'Revenue',
                data: revenueData,
                borderColor: "red",
                backgroundColor: "rgba(0,134,171)"
              },
            ]
          }
        }
      />
    </div>
  )
}