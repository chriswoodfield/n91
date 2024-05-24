#!/usr/bin/env python3

import asyncio
from aiohttp import ClientSession
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import logging
logging.basicConfig(level=logging.INFO)
import pprint
from gql_model import NBModel
from template_model import TemplateModel
from pydantic import ValidationError
import sys
import json
import pdb
import pprint
import jinja2


GQL_ENDPOINT = "http://localhost:8080/api/graphql/"
CSRF_TOKEN_ENDPOINT = "http://localhost:8080/api/"
TOKEN="1dc0438033a3b624e2ddc92995d7d4cd1bdee69a"


class GqlQuery:
    """Run GraphQL query."""
    
    async def _fetch_csrf_token(self, session: ClientSession, url: str) -> str:
        # Need to include text/html header, otherwise cookie is not generated
        async with session.head(url, headers={"Accept":"text/html"}) as response:
            # Extract the CSRF token from the cookies
            csrf_token = response.cookies.get('csrftoken').value
            print(f"DEBUG: csrf_token = {csrf_token}")
            return csrf_token


    async def fetch_data(self, query_str) -> dict:
        """Execute the GraphQL query."""
        # Create a client using the defined transport
        async with ClientSession() as session:
            # Fetch the CSRF token
            csrf_token = await self._fetch_csrf_token(session, CSRF_TOKEN_ENDPOINT)

            # Define the transport with a Nautobot server URL and token authentication
            transport = AIOHTTPTransport(url=GQL_ENDPOINT,
                                        headers={
                                            "X-CSRFToken": csrf_token,
                                            "Authorization": f"Token {TOKEN}"
                                        },
                                        cookies={'csrftoken': csrf_token}
                                        )

            # BGP data
            async with Client(transport=transport, fetch_schema_from_transport=False) as gql_session:
                # Execute the query on the transport
                result = await gql_session.execute(gql(query_str))
                print("")
                print(json.dumps(result, indent=2))
            
            return result


class Generator:
    """Generates GQL queries, marshales into j2 template data"""

    async def get_device_data(self, device_name) -> NBModel.Device:
        
        device_query_str = f"""
        {{
            devices(name: "{device_name}") {{
                name
                _custom_field_data
                interfaces {{
                    name
                    tags {{
                        name
                    }}         
                    ip_addresses {{
                        ip_version
                        address
                    }}
                    untagged_vlan {{
                        vid
                    }}
                    connected_interface {{
                        name
                        ip_addresses {{
                            ip_version
                            address
                        }}
                        device {{
                            name
                        _custom_field_data
                        }}
                    }}
                }}
            }}
        }}
        """      
        
        g = GqlQuery()
        gql_result = await g.fetch_data(device_query_str)
        try:
            model = NBModel.DeviceList.model_validate(gql_result)
        except ValidationError as e:
            pprint.pprint(e.errors())
            sys.exit(1)      
            
        # This query will return only one device
        return model.devices[0]

    async def build_model(self, device_name: str) -> list[NBModel.IPAddress]:
        """Create dict in format to feed to j2 template"""
        
        device_model = await self.get_device_data(device_name)
        
        # Populate vars to feed into object
        device_name = device_model.name
        # Only one mgmt ip
        mgmt_ip_list = await self.get_int_ips(interface_name="Management0",
                                            device_name = device_name, ip_version=4)
        mgmt_ip = mgmt_ip_list[0]
        bgp_asn = device_model.custom_field_data.bgp_asn
        lo_addresses = {"lo_ip4": await self.get_int_ips(interface_name="Loopback0", 
                                            device_name = device_name, ip_version=4),
                        "lo_ip6": await self.get_int_ips(interface_name="Loopback0", 
                                            device_name = device_name, ip_version=6)}
        # Grab the first v4 address without mask
        lo_ip4_addr = lo_addresses["lo_ip4"][0].split("/")[0]
        vxlan_flood_ips = await self.get_vxlan_flood_ips(await self.get_device_by_role(device_role="switch_leaf"))
        vxlan_vlans = await self.get_vlan_list(device_model = device_model)
        access_interfaces = await self.get_access_interfaces(device_model = device_model)
        fabric_interfaces = await self.get_fabric_interfaces(device_model = device_model)
        bgp_neighbors = await self.get_peer_info(device_model = device_model)
                
        # Build the model
        template_data = TemplateModel.Device.model_validate({
            "hostname": device_name,
            "mgmt_ip": mgmt_ip,
            "bgp_asn": bgp_asn,
            "lo_addresses": lo_addresses,
            "lo_ip4_addr": lo_ip4_addr,
            "vxlan_flood_ips": vxlan_flood_ips,
            "vxlan_vlans": vxlan_vlans,
            "access_interfaces": access_interfaces,
            "fabric_interfaces": fabric_interfaces,
            "bgp_neighbors": bgp_neighbors
        })    
    
        #pdb.set_trace()
        return template_data
    
    async def render(self, model_data, template_path):
        # Load Jinja2 template from file
        with open(template_path, 'r') as template_file:
            template_content = template_file.read()
        
        template = jinja2.Template(template_content)
        return template.render(model_data.model_dump())
    
    async def get_int_ips(self, interface_name: str, device_name: str, ip_version: int = 0) -> list[str]:
        """Retrieve IPs for a specific interface of a given device."""
        g = GqlQuery()
        query_str = f"""
        {{
            devices(name: "{device_name}") {{
                name
                interfaces(name: "{interface_name}") {{
                    name
                    ip_addresses {{
                        ip_version
                        address
                    }}
                }}
	        }}
        }}
        """
        try:
            result = NBModel.DeviceList.model_validate(await g.fetch_data(query_str))
        except ValidationError as e:
            pprint.pprint(e.errors())
            sys.exit(1)      
            
        # Given the query was for a single interface, there will only be one list element.
        interface = result.devices[0].interfaces
        
        if ip_version == 0:
            return interface.ip_addresses
        # Filter on version if requested
        else:
            return list(ip_address.address for ip_address in 
                     interface[0].ip_addresses if ip_address.ip_version == ip_version)
        
    async def get_device_by_role(self, device_role: str) -> list[str]:
        """Get list of device names matching a given role."""
        g = GqlQuery()
        query_str = f"""
        {{
            devices(role: "{device_role}") {{
                name
            }}
        }}
        """
        try: 
            result = NBModel.DeviceList.model_validate(await g.fetch_data(query_str))
        except ValidationError as e:
            pprint.pprint(e.errors())
            sys.exit(1)      
            
        
        return [device.name for device in result.devices]

    async def get_vxlan_flood_ips(self, device_list: list[str]) -> str:
        """Returns the IPv6 loopbacks of given devices in a space-separate format."""
        ip_list = ""
        for device_name in device_list:
            ip_address_list = await self.get_int_ips(interface_name="Loopback0", 
                                            device_name = device_name, ip_version=6)
            # Only need the first
            ip_list = ip_list + f"{ip_address_list[0]} "
        
        # trim trailing whitespace
        return ip_list[:-1]

    async def get_vlan_list(self, device_model: NBModel.Device) -> list[int]:
        vlan_list = []
        for interface in device_model.interfaces:
            # Filter on tag name
            if ("interface-access" in list(tag.name for tag in interface.tags)) and \
            (interface.untagged_vlan.vid):
                vlan_list.append(interface.untagged_vlan.vid)

        return vlan_list

    async def get_access_interfaces(self, device_model: NBModel.Device) -> list[dict]:
        interface_list = []
        for interface in device_model.interfaces:
            # Filter on tag name
            if "interface-access" in list(tag.name for tag in interface.tags):
                interface_list.append({
                    "name": interface.name,
                    "description":
                        f"{interface.connected_interface.device.name}:{interface.connected_interface.name}",
                    "vlan_id": interface.untagged_vlan.vid
                })
        return interface_list

    async def get_fabric_interfaces(self, device_model: NBModel.Device) -> list[dict]:
        interface_list = []
        for interface in device_model.interfaces:
            # Filter on tag name
            if "interface-fabric" in list(tag.name for tag in interface.tags):
                interface_list.append({
                    "name": interface.name,
                    "description":
                        f"{interface.connected_interface.device.name}:{interface.connected_interface.name}",
                    "ip4_addr": await self.get_int_ips(interface_name = interface.name, device_name = device_model.name, ip_version = 4),
                    "ip6_addr": await self.get_int_ips(interface_name = interface.name, device_name = device_model.name, ip_version = 6)
                })
                
        return interface_list
                
    async def get_peer_info(self, device_model: NBModel.Device) -> dict[list]:
        """Get connected interface information for BGP Peerings"""
        peer_dict = {"bgp_neighbors_ip4": [], "bgp_neighbors_ip6": []}
        for interface in device_model.interfaces:
            # Filter on tag name
            if "interface-fabric" in list(tag.name for tag in interface.tags):
                remote_asn = interface.connected_interface.device.custom_field_data.bgp_asn
                for ip_address in interface.connected_interface.ip_addresses:
                    if ip_address.ip_version == 4:
                        peer_dict["bgp_neighbors_ip4"].append({"addr": ip_address.address,
                                                                "asn": remote_asn})
                    elif ip_address.ip_version == 6:
                        peer_dict["bgp_neighbors_ip6"].append({"addr": ip_address.address,
                                                                "asn": remote_asn})
                        
        return peer_dict


# Run the async function
async def main():
    device_name = sys.argv[1]
    g = Generator()
    model = await g.build_model(device_name)
    # Get template filename from device name
    if "leaf" in device_name:
        template_name = "templates/leaf_template.j2"
    elif "spine" in device_name:
        template_name = "templates/spine_template.j2"

    print(await g.render(model, template_name))
    
    
if __name__ == "__main__":
    asyncio.run(main())