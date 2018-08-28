#!/usr/bin/env python3
# Author: Micah Martin
"""
This script generates topology information in the following format:

{
    "name": "ISTS16",
    "Date": "2/2/2018",
    "teams": {
        1: {
            "networks": {
                "local": {
                    "scheme": "10.2.X",
                    "hosts": {
                        "ad": {
                            "ip": "10.2.1.10",
                            "platform": "windows",
                            "os": "server 2016",
                            "services": {
                                "ldap": {"port": 389, "scored": True},
                                "smb": {"port": 445, "scored": False},
                            },
                        },
                        "web": {
                            "ip": "10.2.1.20",
                            "platform": "linux",
                            "os": "ubuntu",
                            "services": {
                                "http": {"port": 80, "scored": True},
                                "ssh": {"port": 22, "scored": True},
                            },
                        },
                    },
                }
            }
        }
    },
}
"""

# import json
# import yaml

from copy import deepcopy
from functools import wraps
from pprint import pprint
from typing import Union, List, Dict
from termcolor import colored as c

COLOR = "blue"
# Type aliases
SERVICE = Dict[str, Dict[str, Union[str, int, bool]]]
SERVICES = Dict[str, SERVICE]
HOST = Dict[str, Union[str, SERVICES]]
HOSTS = Dict[str, HOST]
NETWORK = Dict[str, Union[str, HOSTS]]
TEAM = Dict[str, NETWORK]
TEAMS = Dict[int, TEAM]


def confirm(func):
    """
    Function wrapper used to confirm the functions result before continuing.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            try:
                retval = func(*args, **kwargs)
                print("\n")
                pprint(retval)
                if yes_no_prompt("Correct?"):
                    print("\n")
                    return retval
            except Exception:
                print("Invalid input")

    return wrapper


def prompt(text: str = "", color: str = COLOR) -> str:
    """
    Generate a prompt with the given color and return the output
    """
    return input(c(text, color, attrs=("bold",)))


def yes_no_prompt(msg: str) -> bool:
    """
    Returns True for yes and False for no.
    """
    value = prompt(f"{msg} [Y/n]", "green")
    return value in ("", "y", "yes")


@confirm
def get_team_ids() -> List[int]:
    """
    Generate a list of the team numbers based on starting and ending values
    """
    start = int(prompt("Starting team number: "))
    end = int(prompt("Ending team number: "))
    return [i for i in range(start, end + 1)]


@confirm
def add_service() -> SERVICE:
    """
    Creates a service for a host.
    """
    print("\nAdding Service:")
    name = prompt("Service (e.g. http): ").lower()
    port = int(prompt("Port (e.g. 80): ").lower())
    scored = yes_no_prompt("Scored?")
    return {"name": name, "port": port, "scored": scored}


@confirm
def add_host(scheme) -> HOST:
    """
    Get the input information for a host on the network
    """
    print("\nAdding Host:")
    name = prompt("Name: ")
    ip = input(c("IP: ", COLOR, attrs=("bold",)) + scheme + ".")
    platform = prompt("Platform (e.g. windows/linux): ")
    os = prompt("OS (e.g. Server 2016/Ubuntu 16): ")
    services = {}
    while True:
        if not yes_no_prompt("Add service?"):
            break

        service = add_service()
        if service:
            services[service["name"]] = {"port": service["port"], "scored": service["scored"]}
    return {
        "name": name,
        "ip": f"{scheme}.{ip}",
        "platform": platform,
        "os": os,
        "services": services,
    }


@confirm
def add_network() -> NETWORK:
    """
    Add a network for all teams to the topology.
    """
    print("\nAdding Network:")
    name = prompt("Name: ")
    print("Please enter an appropriate scheme. The 'X' will be replaced with the team id.")
    scheme = prompt("IP Scheme (e.g. '10.2.X')").upper()
    scheme.index("X")
    hosts = {}
    while True:
        host = add_host(scheme)
        if host:
            hosts[host["name"]] = {
                "ip": host["ip"],
                "platform": host["platform"],
                "services": host["services"],
            }
        if not yes_no_prompt("Add another host?"):
            break
    return {"name": name, "scheme": scheme, "hosts": hosts}


def add_networks() -> TEAM:
    """
    Loop and add networks based on an IP scheme.
    """
    networks = {}
    while True:
        network = add_network()
        if network:
            networks[network["name"]] = {"scheme": network["scheme"], "hosts": network["hosts"]}
        if not yes_no_prompt("Continue adding networks?"):
            break
    return networks


def build_topology(team_ids: List[int], networks: TEAM) -> TEAMS:
    config = {}
    for team_id in team_ids:
        team_networks = deepcopy(networks)
        for network in team_networks.values():
            for host in network["hosts"].values():
                host["ip"] = host["ip"].replace("X", str(team_id))
        config[team_id] = deepcopy(team_networks)

    return config


def main() -> None:
    """
    Call all the generate functions and build a json config
    """
    # Get the teams
    team_ids = get_team_ids()

    # Get the networks
    networks = add_networks()

    # net = {'somenet': {'scheme': '10.1.X', 'hosts': {'bob': {'ip': '10.1.X.10'}}}}
    # Build topology
    config = build_topology(team_ids, networks)
    pprint(config)

    # print(json.dumps(config, indent=4))
    # print(yaml.dump(config, default_flow_style=False))


if __name__ == "__main__":
    main()
