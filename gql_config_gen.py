#!/usr/bin/env python3

import asyncio
from aiohttp import ClientSession, ClientResponse
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import logging
logging.basicConfig(level=logging.DEBUG)

GQL_ENDPOINT = "https://demo.nautobot.com/graphql/"
#GQL_ENDPOINT = "http://localhost:8080/graphql/"
CSRF_TOKEN_ENDPOINT = "https://demo.nautobot.com/api/"
#CSRF_TOKEN_ENDPOINT = "http://localhost:8080/api/"
#TOKEN="foobar"
TOKEN="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
#TOKEN="1234567890123456789012345678901234567890"
HOST="leaf1"

#query_str = f"""
#{{
#    devices(name: "{HOST}") {{
#        interfaces(tags: "interface-spine-leaf") {{
#            name
#            ip_addresses {{
#                address
#            }}
#            connected_interface {{
#                name
#                ip_addresses {{
#                    ip_version
#                    address
#                }}
#                device {{
#                    name
#                   _custom_field_data
#                }}
#            }}
#        }}
#    }}
#}}
#"""

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
        print(f"DEBUG: csrf_token = {csrf_token}")
        return csrf_token

async def fetch_data() -> None:

    query = gql(query_str)

    # Create a client using the defined transport
    async with ClientSession() as session:
        # Fetch the CSRF token
        csrf_token = await fetch_csrf_token(session, CSRF_TOKEN_ENDPOINT)

        # Define the transport with a Nautobot server URL and token authentication
        transport = AIOHTTPTransport(url=GQL_ENDPOINT,
                                    headers={
                                        "X-CSRFToken": csrf_token,
                                        "Authorization": f"Token {TOKEN}"
                                    },
                                    cookies={'csrftoken': csrf_token}
                                    )

        print("DEBUG: query_str:")
        print(query_str)

        async with Client(transport=transport, fetch_schema_from_transport=False) as gql_session:
            # Execute the query on the transport
            result = await gql_session.execute(query)
            print(result)

# Run the async function
asyncio.run(fetch_data())