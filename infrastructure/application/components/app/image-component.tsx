import Image from "next/image"


export const ImageComponent = () => {
  return (
    <Image
      src="/products/tsla-img.png"
      alt="tsla product"
      width={350}
      height={350}
    />
  )
}