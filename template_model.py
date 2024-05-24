from __future__ import annotations
from pydantic import BaseModel
from gql_model import NBModel

class TemplateModel:
    
    class BGPNeighbor(BaseModel):
        addr: str
        asn: int

    
    class Interface(BaseModel):
        name: str
        description: str
        ip4_addr: list[str] = []
        ip6_addr: list[str] = []
        vlan_id: int = None    
        
        
    class BGPNeighborList(BaseModel):
        bgp_neighbors_ip4: list[TemplateModel.BGPNeighbor]
        bgp_neighbors_ip6: list[TemplateModel.BGPNeighbor]
       
        
    class LoopbackAddressList(BaseModel):
        lo_ip4: list[str] = []
        lo_ip6: list[str] = []
        
        
    class Device(BaseModel):
        hostname: str
        vxlan_vlans: list[int] = []
        access_interfaces: list[TemplateModel.Interface] = []
        fabric_interfaces: list[TemplateModel.Interface]
        lo_addresses: TemplateModel.LoopbackAddressList
        lo_ip4_addr: str
        vxlan_flood_ips: str = None
        mgmt_ip: str
        bgp_asn: str
        bgp_neighbors: TemplateModel.BGPNeighborList = None
        
    
    