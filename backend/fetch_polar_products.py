import asyncio
from polar_sdk import Polar
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("POLAR_ACCESS_TOKEN")
    if not token:
        print("No token")
        return
    
    polar = Polar(access_token=token)
    
    products = await polar.products.list_async()
    print(products)

if __name__ == "__main__":
    asyncio.run(main())
