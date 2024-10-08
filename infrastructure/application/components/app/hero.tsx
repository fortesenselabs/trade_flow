import { ArrowRight, ChevronRight } from 'lucide-react';
import React from 'react'
import { Button } from '../shadcn-ui/button'
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
const Hero = () => {

  return (
    <div className="flex flex-col items-center pt-[250px] relative">
      <p className="text-[42px] font-semibold">Make easy money with financial investment</p>
      <p className="text-[30px] font-bold">in one <span className="text-[#500480]">DynamiteTrade</span></p>
      <div className="flex flex-col items-center mt-6 text-muted-foreground">
        <p>Browse all stocks, keep track of any stock changes</p>
        <p>and get immediate financial advice from DT advisors</p>
      </div>
      <div className="flex mt-8 space-x-2">
        <Link
          href={"/dashboard"}
        >
          <Button
            variant="default"
            className="pl-5 pr-3 rounded-md">
            <p>Get started</p>
            <ChevronRight className="w-4 h-4 ml-2" />
          </Button>
        </Link>

        <Link
          className='flex items-center gap-2 px-4 py-1 text-sm font-normal shadow-sm text-muted-foreground '
          href="/admin">
          <p>Sign in as Admin</p>
          <ChevronRight className="w-4 h-4" />
        </Link>

      </div>
      <div className='mt-[270px]  bg-black flex justify-center h-[700px] w-full ' >
      </div>
      <div className='absolute bottom-[220px]'>
        <Image
          src='/landing-page/landing-animation.gif'
          alt='landing page animation'
          width={1000}
          height={700}
          className='object-contain '
        />
      </div>

    </div>
  )
}

export default Hero