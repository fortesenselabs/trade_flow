/**
 * Component representing an Accordion container.
 * 
 * This component renders an Accordion component containing multiple AccordionItem components,
 * each displaying different content based on user interaction.
 */

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/shadcn-ui/accordion"
import {
  DoughnutChart,
  PortfolioItem,
  Watchlist
} from './index';

/**
 * Functional component representing an Accordion container.
 * 
 * @returns JSX.Element representing the Accordion container.
 */
export function AccordionContainer() {
  return (
    <Accordion type="multiple" className="w-full" defaultValue={["item-3"]}>
      {/* AccordionItem for Portfolio. */}
      <AccordionItem value="item-1" className="px-4 ">
        <AccordionTrigger className="text-sm font-semibold">Porfolio</AccordionTrigger>
        <AccordionContent>
          <PortfolioItem />
        </AccordionContent>
      </AccordionItem>
      {/* AccordionItem for Watchlist. */}
      <AccordionItem value="item-2" className="px-4">
        <AccordionTrigger className="text-sm font-semibold">Watchlist</AccordionTrigger>
        <AccordionContent>
          <Watchlist />
        </AccordionContent>
      </AccordionItem>
      {/* AccordionItem for Distribution. */}
      <AccordionItem value="item-3" className="px-4 ">
        <AccordionTrigger className="text-sm font-semibold">Distribution</AccordionTrigger>
        <AccordionContent>
          <DoughnutChart />
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  )
}
