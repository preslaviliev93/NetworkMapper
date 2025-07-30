"""
@Author: Peslav Iliev
"""
import subprocess
import platform
import commands_mapper
import re


class NetworkMapper:
    def __init__(self) -> None:
        self.arp_entries = {}
        """
            arp_entries = {
                "device": {
                    "Mac1": "IP address",
                    "Mac2": "IP address", 
                },
                "device2":{
                    "Mac1": "IP address",
                    "Mac2": "IP address",
                },
                ...
            }
        """

    @staticmethod
    def get_os_name() -> str:
        """
        :return: Windows or Linux as a string
        """
        return platform.system()  # Tested on Linux (debian Distributions) and Windows

    def get_all_arp_entries(self, os_name: str) -> str or Exception:
        try:
            return subprocess.run(commands_mapper.cmd_map[os_name]['get_arps'], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True).stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"

    def parse_arp_entries(self, arp_entries: str, os_name: str) -> str:
        """
        We will be using the two helping functions for Linux And Windows
        :param arp_entries:
        :return:
        """
        if os_name not in commands_mapper.cmd_map:
            return f"{os_name} is not Supported"

        parser_function = commands_mapper.cmd_map[os_name]["parser_function"]
        parser_f = getattr(self, parser_function)
        return parser_f(arp_entries)

    def windows_parser(self, arp_entries_string: str) -> str:
        current_net_interface = ""
        for entry in arp_entries_string.split("\n"):
            pattern = r'\bInterface: ((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3})\b'
            match = re.search(pattern, entry)
            if match:
                current_net_interface = match.group(1)

            if current_net_interface not in self.arp_entries and current_net_interface != '':
                self.arp_entries[current_net_interface] = {}

            match_ip_arp_pattern = r'\b((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3})\b.*?\b([0-9A-Fa-f]{2}([-:][0-9A-Fa-f]{2}){5}|[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})\b'
            matches = re.findall(match_ip_arp_pattern, entry)
            for m in matches:
                ip = m[0]
                mac = m[4] if m[4] else 'No Mac'
                if current_net_interface:
                    self.arp_entries[current_net_interface][mac] = ip
        return current_net_interface

    def linux_parser(self, arp_entries_string: str) -> str:
        current_net_interface = ''
        for line in arp_entries_string.splitlines()[1:]:  # skipping the header line
            line_lst = line.split()
            if len(line_lst) < 6:
                continue
            ip = line_lst[0]
            mac = line_lst[3]
            current_net_interface = line_lst[5]

            if current_net_interface not in self.arp_entries and current_net_interface != '':
                self.arp_entries[current_net_interface] = {}
            self.arp_entries[current_net_interface][mac] = ip
        return current_net_interface

    def main(self) -> None:
        all_arps = self.get_all_arp_entries(self.get_os_name())
        self.parse_arp_entries(all_arps, self.get_os_name())
        print(f'Final entries dict is: {self.arp_entries}')


if __name__ == '__main__':
    network_mapper = NetworkMapper()
    network_mapper.main()
