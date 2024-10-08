import Image from 'next/image'
import Link from 'next/link'
import React from 'react'
//This is a layout ui page when open sign-in/sign-up page
const layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex w-full h-screen ">
      <div className='flex items-center justify-center flex-1 gap-4 bg-black'>
        <Image
          src="/landing-page/logo2.png"
          alt="logo"
          width={110}
          height={110}
          className='object-contain'
        />
        <div>
          <p className='text-4xl font-semibold text-white'>DynamiteTrade</p>
          <p className='font-normal text-md text-muted-foreground'>Trade Explosively like never before</p>
        </div>
      </div>

      <div className='flex flex-col items-center justify-center pl-16 pr-12 border-lborder-blue-600/30'>
        <div className='relative'>
          {children}
          <Link
            className='absolute text-sm font-normal underline bottom-4 left-[60px] text-muted-foreground text-blue-800'
            href="/admin">
            Sign in as Admin
          </Link>
        </div>
      </div>
    </div>
  )
}

export default layout