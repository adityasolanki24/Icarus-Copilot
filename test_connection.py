import httpx
import asyncio

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.google.com")
            print(f"Connection successful! Status: {response.status_code}")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())

