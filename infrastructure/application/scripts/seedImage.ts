import { db } from "@/scripts/index"
import { Company } from "@prisma/client";


// Seeds company data into the database
async function seedLogos() {
  try {
    // const companies = await db.company.findMany()
    // await db.company.updateMany({
    //   where: {
    //     logoSrc: '/logos/dummy-logo.webp',
    //   },
    //   data: {
    //     logoSrc: 'dummy-logo.webp',
    //   }
    // })

    await db.company.updateMany({
      where: {
        logoSrc: null
      },
      data: {
        logoSrc: 'dummy-logo.webp'
      }
    })

    const promises1 = []
    const arrLogos = ['jd', 'pypl', 'msft', 'meta', 'wmt', 'ma', 'amzn', 'abnb', 'ebay', 'cola', 'sofi', 'googl', 'tsla', 'nvda', 'aapl', 'amd', 'visa', 'xom', 'shopify', 'salesforce', 'pfizer', 'nike', 'lowes', 'ibm', 'cmcsa', 'citygroup', 'cisco', 'cigna', 'chubb', 'caterpillar', 'ba']
    for (let i = 0; i < arrLogos.length; i++) {
      promises1.push(db.company.update({
        where: {
          symbol: arrLogos[i].toUpperCase()
        },
        data: {
          logoSrc: arrLogos[i] + '.svg'
        }
      }))
    }
    await Promise.all(promises1)
    // const promises = []
    // const arrProducts = ['jd', 'pypl', 'msft', 'meta', 'wmt', 'ma', 'amzn', 'abnb', 'ebay', 'cola', 'sofi', 'googl', 'tsla', 'nvda', 'aapl', 'amd', 'visa']

    // for (let i = 0; i < arrProducts.length; i++) {
    //   promises.push(db.company.update({
    //     where: {
    //       symbol: arrProducts[i].toUpperCase()
    //     },
    //     data: {
    //       productSrc: arrProducts[i] + '.webp'
    //     }
    //   }))
    // }
    // console.log(arrProducts.length)
    // console.log("actual" + promises.length)
    // await Promise.all(promises);
    console.log("seeding company data successfully");
  } catch (error) {
    console.log("error seeding company data", error)
  }
}

seedLogos()

export default seedLogos
// npx tsx scripts/seedImage.ts