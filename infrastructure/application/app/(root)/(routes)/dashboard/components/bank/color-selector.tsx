import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn-ui/select"
import { useColor } from "@/hooks/use-color";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { HexColorPicker } from "react-colorful";
import { useRef } from "react";

export const ColorSelector = () => {
  const { color, setColor } = useColor()
  const [isOpen, setIsOpen] = useState(false);
  const presetColors = ["#5b13f4", "#5b4ff4", "#bb4ff4", "#bb4f99", "#00b59d", "#b8b198"];

  const handleClick = (input: string) => {
    setColor(input)
  }
  return (
    <Select open={isOpen} onOpenChange={setIsOpen}>
      <SelectTrigger className="w-[160px]" onClick={() => setIsOpen(true)}>
        {color === "" ? <SelectValue
          placeholder="Select color" /> :
          <>
            <div style={{ backgroundColor: color }} className={`w-[20px] h-[20px]`}></div>
            <div>{color}</div>
          </>}
      </SelectTrigger>
      <SelectContent className="z-[2000]">
        <SelectGroup>
          <SelectItem value={color === "" ? "#ffffff" : color} >
            <HexColorPicker onChange={setColor} color={color}
            />
          </SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}
