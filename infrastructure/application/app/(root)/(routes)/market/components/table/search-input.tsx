import { Input } from "@/components/shadcn-ui/input"
import { Search } from "lucide-react"
import { useEffect, useState, ChangeEventHandler } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import qs from "query-string";



export const SearchInput = () => {

  const router = useRouter();
  const searchParams = useSearchParams();

  const symbol = searchParams.get("symbol");

  const [value, setValue] = useState(symbol || "");

  const onChange: ChangeEventHandler<HTMLInputElement> = (e) => {
    setValue(e.target.value);
  };

  useEffect(() => {
    const query = {
      symbol: value
    };

    const url = qs.stringifyUrl({
      url: window.location.href,
      query
    }, { skipNull: true, skipEmptyString: true });

    router.push(url);
  }, [value, router])

  return (
    <div className="p-2 w-[40%] relative">
      <Input
        onChange={onChange}
        value={value}
        placeholder="Enter stock symbol..."
        className="pl-2 mb-1"
      />
    </div>
  )
}