import React from 'react'
import BotAvatar from './BotAvatar'

const SideContent = () => {
  return (
    <div className='py-2'>
      <p className='px-4'>1 Message</p>
      <div className='flex items-center gap-2 p-4 mt-4 border border-muted-foreground/30 bg-muted-foreground/5'>
        <BotAvatar />
        <p>Dynamite ChatBot</p>
      </div>

    </div>
  )
}

export default SideContent