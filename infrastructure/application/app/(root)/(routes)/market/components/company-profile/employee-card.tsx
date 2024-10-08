import React from 'react'

interface EmployeeCardProps {
  data: {
    amount: string,
    name: string
  }
}

const EmployeeCard = ({ data }: EmployeeCardProps) => {
  const { amount, name } = data;
  return (
    <div className=' w-[110px] h-[120px] flex flex-col items-center justify-between shadow-lg py-8 rounded-lg dark:shadow-orange-600 dark:shadow-sm'>
      <p>{name}</p>
      <p>{amount}</p>
    </div>
  )
}

export default EmployeeCard