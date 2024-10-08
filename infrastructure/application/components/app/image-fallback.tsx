import React, { useState } from 'react';
import Image from 'next/image';

interface ImageWithFallbackProps {
  props: {
    src: string,
    fallbackSrc: string,
    width: number,
    height: number,
    className: string
  }
}
const ImageWithFallback = ({ props }: ImageWithFallbackProps) => {
  const { src, fallbackSrc, width, height } = props;
  const [imgSrc, setImgSrc] = useState(src);

  return (
    <Image
      width={width}
      height={height}
      src={imgSrc}
      alt='product img'
      onError={() => {
        setImgSrc(fallbackSrc);
      }}
    />
  );
};

export default ImageWithFallback;