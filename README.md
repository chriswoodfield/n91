This is a series of challenges utilizing Nautobot's GraphQL API.

GraphQL is a powerful query language for APIs that allows for descriptive and
efficient data queries. Utilizing JSON-formatted queries over HTTP, it allows 
clients to ask for specific data elements and attributes, and to make complex 
queries that span multiple tables (much like SQL JOINs, but utilizing heirarchial
JSON structures to make these easier to work with).

Nautobot's GraphQL API can be queried via its own web UI on the server at
https://hostname/graphql:

(pic here)

The query language follows the same keys that are exposed by Nautobot's REST API. However,
under GraphQL, only the requested keys are returned in the reply:

(pic here)

Where a JSON query normally returns object IDs for associated elements which must be queried separately, the GraphQL
implementation allows for a query that can include elements from those references objects.

GraphQL queries can be filtered by values in any of the object's fields, such as name, tags, role, or similar. 
Use the Nautobot demo site at https://demo.nautobot.com/graphql with the following query:

```
{
  devices(name: "ams01-edge-01") {
    name
    id
    interfaces {
      name
      id
      ip_addresses {
        id
        ip_version
        address
      }
    }
  }
}
```

CHALLENGE 1:
Write a GraphQL query that returns the names and id values of all devices that are in the site named "MCI1".
These should be the only values returned by the query. Extraneous data will not be accepted as part of the solution.
Submit the results of the query to CTFd.

CHALLENGE 2:
Write a QraphQL query that returns data about a device named "spine1". The return data should consist of:
- device id
- device name
- The IPv4 and IPv6 addresses/masks assigned to the "Ethernet1" interface.

Note: The above data points should be the *only* data returned by the query. Submit the results of the query to CTFd.

CHALLENGE 3:
Write a GraphQL query that for the device named "leaf1", returns the following data:
- The IPv4 and IPv6 addresses of each connected device for interfaces with the "interface-fabric" tag assigned.
- The hostname and bgp_asn custom field value for the connected device.

Note: The above data points should be the *only* data returned by the query. Submit the results of the query to CTFd.

CHALLENGE 4:
Given the included jinja2 template, write a python script that usese GraphQL to query the above data, then renders a BGP configuration section via jinja2.
Submit the resulting configuration text to CTFd.