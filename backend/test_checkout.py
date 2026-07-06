import asyncio
from polar_sdk import Polar
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

async def main():
    token = os.getenv("POLAR_ACCESS_TOKEN")
    polar = Polar(access_token=token)
    
    try:
        checkout = await polar.checkouts.create_async(
            request={
                "product_id": "66251480-56d8-4b7f-887b-8fe291f8e340",
                "success_url": "http://localhost:3000/dashboard?checkout=success"
            }
        )
        print("Success!")
        print(checkout.url)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
