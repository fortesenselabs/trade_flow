"use client"

import { DeepPartial, LastPriceAnimationMode, TimeChartOptions, createChart } from 'lightweight-charts';
import { useRef, useEffect } from 'react';

export const LineChart = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const upTrend = true;
  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const chartOptions: DeepPartial<TimeChartOptions> = {
      layout: {
        textColor: 'black',
        background: {
          color: 'transparent'
        }
      },
      grid: {
        vertLines: {
          visible: false
        },
        horzLines: {
          visible: false
        }
      },
      rightPriceScale: {
        visible: false
      },
      timeScale: {
        visible: false
      }
    };
    const chart = createChart(containerRef.current, chartOptions);

    const areaSeries = chart.addLineSeries({ color: upTrend ? '#14a34a' : '#ea2c2b', lastPriceAnimation: LastPriceAnimationMode.Continuous, priceLineVisible: false });

    areaSeries.setData([
      { time: '2018-12-22', value: 22.51 },
      { time: '2018-12-23', value: 23.11 },
      { time: '2018-12-24', value: 25.02 },
      { time: '2018-12-25', value: 27.32 },
      { time: '2018-12-26', value: 24.17 },
      { time: '2018-12-27', value: 23.89 },
      { time: '2018-12-28', value: 28.46 },
      { time: '2018-12-29', value: 29.92 },
      { time: '2018-12-30', value: 35.68 },
      { time: '2018-12-31', value: 40.67 },
    ]);

    chart.timeScale().fitContent();
  }, [])

  return (
    <div ref={containerRef} className="w-[80px] h-[50px]"></div>
  )
}