# :point_right: Introduction

DynamiteTrade is an opensource financial project aiming to provide a clean and snappy user interface to view stock information of companies in (soft) real time.
The project is written in JavaScript/TypeScript leveraging full stack framework NextJS and deploying on Vercel hosting platform.

Here is the site: [https://dynamitetrade.vercel.app/](https://dynamitetrade.vercel.app/)

<img src='https://github.com/longleDevops/Financial-App/blob/main/public/landing-page/landingpage-animation2.gif'>

## :zap: Tech Stack

<details open>
<summary>Client</summary>

* Typescript
* Tailwind CSS
* Clerk
* Shadcn-UI
* Aceternity-UI
* Chart.JS

</details>

<details open>
<summary>Server</summary>

* Typescript
* NextJS
* Tanstack Query
* ChatGPT-3,5 Turbo

</details>

<details open>
<summary>Database</summary>

* Postgresql
* Supabass
* Prisma

</details>

<details open>
<summary>Hosting</summary>

* Vercel

</details>

## :pushpin: Features 

- ChatGPT-3.5 Bot
- Light/dark mode toggle
- Buy/sell stocks 
- Add/remove stocks from watchlist
- View transaction records
- Add/remove customizable cards
- Deposit/withdraw from trading account
- Authentication
- Search stocks
- View stock prices & company history

## :key: Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`YAHOO_FINANCE_STOCK_SUMMARY`

`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`

`CLERK_SECRET_KEY`

`NEXT_PUBLIC_CLERK_SIGN_IN_URL`

`NEXT_PUBLIC_CLERK_SIGN_UP_URL`

`NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`

`NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`

`DATABASE_URL`

`DIRECT_URL`

# :hammer: Build

This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.

## Project Layout

```
└──./
    ├──app/
    │   ├──(auth)/
    │   │   ├──(routes)/
    │   │   │   ├──sign-in/
    │   │   │   │   └──[[...sign-in]]/
    │   │   │   └──sign-up/
    │   │   │       └──[[...sign-up]]/
    │   ├──(landing-page)/
    │   ├──(root)/
    │   │   ├──(routes)/
    │   │   │   ├──chat/
    │   │   │   │   ├──components/
    │   │   │   ├──dashboard/
    │   │   │   │   ├──components/
    │   │   │   │   │   ├──accordion/
    │   │   │   │   │   ├──account/
    │   │   │   │   │   ├──bank/
    │   │   │   │   │   ├──not-use/
    │   │   │   │   │   ├──table/
    │   │   │   └──market/
    │   │   │       ├──components/
    │   │   │       │   ├──company-profile/
    │   │   │       │   ├──company-table/
    │   │   │       │   ├──products/
    │   │   │       │   └──transaction/
    │   ├──api/
    │   │   ├──account/
    │   │   ├──chat/
    │   │   ├──dashboard-watchlist/
    │   │   ├──market-watchlist/
    │   │   └──portfolio/
    ├──components/
    │   ├──aceternity-ui/
    │   ├──shadcn-ui/
    │   └──ui/
    ├──constants/
    ├──hooks/
    ├──lib/
    ├──prisma/
    ├──providers/
    ├──public/
    │   ├──avatars/
    │   ├──employees/
    │   ├──logos/
    │   ├──products/
    ├──scripts/
    ├──types/
    └──utils/
```


## :green_book: API Reference

#### Get account

```http
  GET /api/account
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `N/A` | `Object` | **Get** user account from the database |

#### Get portfolio

```http
  GET /api/portfolio
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `N/A` | `Object` | **Get** user portfolio from the database |

#### Update portfolio

```http
  PATCH /api/portfolio
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `N/A`      | `void` | **Update** the value of user's portfolio|

#### Get transaction

```http
  GET /api/transaction
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `N/A` | `Object[]` | **Get** a list of transactions from the database |

#### Buy stock

```http
  POST /api/transaction/buy
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `N/A` | `void` | **Execute** the 'buy' function |

#### Sell stock

```http
  POST /api/transaction/sell
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `N/A` | `void` | **Execute** the 'sell' function |



## ER Diagram

<img src='https://github.com/longleDevops/logo-images/blob/main/DynamiteTrade%20-%20Frame%201.jpg'  >

## Architecture

<img src='https://github.com/longleDevops/Financial-App/blob/main/doc/architecture.svg' width='600' >

## Classes

<img src='https://github.com/longleDevops/Financial-App/blob/main/doc/class.svg' width='600' >

