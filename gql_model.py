#!/usr/bin/env python3

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
import pdb


class NBModel:
    
    
    class BGPAsn(BaseModel):
        bgp_asn: Optional[str] = None


    class IPAddress(BaseModel):
        ip_version: int
        address: str


    class ConnectedInterface(BaseModel):
        device: NBModel.Device
        name: str
        ip_addresses: list[NBModel.IPAddress] = None


    class Tag(BaseModel):
        name: str


    class Interface(BaseModel):
        name: str
        tags: list[NBModel.Tag] = []
        ip_addresses: list[NBModel.IPAddress] = None
        connected_interface: Optional[NBModel.ConnectedInterface] = None
        untagged_vlan: Optional[NBModel.Vlan] = None


    class Vlan(BaseModel):
        vid: int


    class Device(BaseModel):
        name: str
        custom_field_data: NBModel.BGPAsn = Field(None, alias="_custom_field_data")
        interfaces: list[NBModel.Interface] = None

        
    class DeviceList(BaseModel):
        devices: list[NBModel.Device]
