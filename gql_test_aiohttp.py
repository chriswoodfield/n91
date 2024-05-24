#!/usr/bin/env python3

import asyncio
from aiohttp import ClientSession, ClientResponse
import logging
logging.basicConfig(level=logging.DEBUG)

GQL_ENDPOINT = "http://localhost:8080/graphql/"
CSRF_TOKEN_ENDPOINT = "http://localhost:8080/api/"
TOKEN="foobar"
#TOKEN="1234567890123456789012345678901234567890"

query_str = """
query {
    devices {
        name
        id
    }
}
"""

async def fetch_csrf_token(session: ClientSession, url: str) -> str:
    # Need to include text/html header, otherwise cookie is not generated
    async with session.head(url, headers={"Accept":"text/html"}) as response:
        # Extract the CSRF token from the cookies
        csrf_token = response.cookies.get('csrftoken').value
        print(f"DEBUG:csrf_token = {csrf_token}")
        return csrf_token

async def fetch_data() -> None:

    # Create a client using the defined transport
    async with ClientSession() as session:
        # Fetch the CSRF token
        csrf_token = await fetch_csrf_token(session, CSRF_TOKEN_ENDPOINT)

    headers= {"X-CSRFToken": csrf_token,
                "Authorization": f"Token {TOKEN}"}
    cookies = {"csrftoken": csrf_token}

    async with ClientSession(headers=headers, cookies=cookies) as session:
        print("DEBUG:query_str:")
        print(query_str)

        async with session.post(GQL_ENDPOINT, json={"query": query_str}) as resp:
            json_body = await resp.json()
        
        print(json_body)
            

# Run the async function
asyncio.run(fetch_data())