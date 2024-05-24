import httpx

url = "https://demo.nautobot.com/api/graphql/"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Token aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}

query = """
{
    devices {
        name
        device_type {
        manufacturer {
            name
        }
        }
    }
}
"""

response = httpx.post(url, headers=headers, json={"query": query})

import pdb; pdb.set_trace()