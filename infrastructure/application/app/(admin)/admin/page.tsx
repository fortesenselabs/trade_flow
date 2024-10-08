"use client"
import { Authentication } from "./components/authentication"
import { useState } from "react"
import { Contents } from "./components/contents"
const AdminPage = () => {
  const [isSuccess, setIsSuccess] = useState(false)
  return (
    <>
      {!isSuccess ?
        <Authentication isSuccess={isSuccess} setIsSuccess={setIsSuccess} /> :
        <Contents />
      }
    </>
  )
}

export default AdminPage