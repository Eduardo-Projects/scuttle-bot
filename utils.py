import aiohttp
import asyncio


async def make_riot_api_request(url, success_handler=None, *args, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Check if a success_handler is provided
                if success_handler:
                    result = await success_handler(data, *args, **kwargs)
                    return result
                # Directly return data or perform another action if no handler is provided
                else:
                    return data
            elif response.status == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                print(f"Rate limit exceeded. Retrying in {retry_after} seconds.")
                await asyncio.sleep(retry_after)
                return await make_riot_api_request(
                    url, success_handler, *args, **kwargs
                )
            elif response.status in {400, 401, 403, 404}:
                raise ValueError("Match not found.")
            else:
                response.raise_for_status()


# generic success handler
async def handle_key_success(data, key):
    return data[key]
