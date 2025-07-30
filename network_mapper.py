"""
@Author: Peslav Iliev
"""
import subprocess
import platform
import commands_mapper
import re
import drawio
import math

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
        self.current_os_name = self.get_os_name()

    @staticmethod
    def get_os_name() -> str:
        """
        :return: Windows or Linux as a string
        """
        return platform.system()  # Tested on Linux (debian Distributions) and Windows

    def get_all_arp_entries(self) -> str or Exception:
        try:
            return subprocess.run(commands_mapper.cmd_map[self.current_os_name]['get_arps'], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True).stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"

    def parse_arp_entries(self, arp_entries: str) -> str:
        """
        We will be using the two helping functions for Linux And Windows
        :param arp_entries:
        :return:
        """
        if self.current_os_name not in commands_mapper.cmd_map:
            return f"{self.current_os_name} is not Supported"

        parser_function = commands_mapper.cmd_map[self.current_os_name]["parser_function"]
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
                mac = m[4]
                if current_net_interface and self.check_if_is_active(ip):
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
            if self.check_if_is_active(ip):
                self.arp_entries[current_net_interface][mac] = ip
        return current_net_interface

    def check_if_is_active(self, ip: str) -> bool:
        ping_cmd = commands_mapper.cmd_map[self.current_os_name]['pinger'] + [ip]
        print(f"Checking if {ip} is active...")
        result = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0

    def get_vendor_by_mac(self, mac: str) -> str:
        """
        This can be extended if you have access to any mac address to vendor API
        :param mac:
        :return:
        """
        ...

    def generate_drawio(self, current_interface, filename="network_map.drawio"):
        xml_header = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<mxfile host="app.diagrams.net">\n'
            '  <diagram name="Network Topology">\n'
            '    <mxGraphModel>\n'
            '      <root>\n'
            '        <mxCell id="0"/>\n'
            '        <mxCell id="1" parent="0"/>\n'
        )
        cell_id = 2
        connections = []

        pc_style = "fontColor=#0066CC;verticalAlign=top;verticalLabelPosition=bottom;labelPosition=center;align=center;html=1;outlineConnect=0;strokeWidth=2;shape=mxgraph.networks.pc;"

        normal_pc = pc_style + "fillColor=#FFFFFF;strokeColor=#6881B3;gradientColor=none;"
        broadcast_pc = pc_style + "fillColor=#CCCCCC;strokeColor=#888888;gradientColor=none;"
        current_pc = pc_style + "fillColor=#A3E4A3;strokeColor=#2E8B57;gradientColor=none;"  # green
        gateway_pc = pc_style + "fillColor=#D6EAF8;strokeColor=#2874A6;gradientColor=none;"  # blue


        center_id = cell_id
        xml_header += (
            f'        <mxCell id="{center_id}" value="Network Core" style="{normal_pc}" vertex="1" parent="1">\n'
            f'          <mxGeometry x="600" y="400" width="100" height="100" as="geometry"/>\n'
            f'        </mxCell>\n'
        )
        cell_id += 1


        all_devices = []
        for iface, devices in self.arp_entries.items():
            all_devices.append((iface, iface, True))
            for mac, ip in devices.items():
                all_devices.append((ip, mac, False))

        # Arrange in circle
        radius = 500
        angle_step = (2 * math.pi) / max(1, len(all_devices))
        angle = 0

        for ip, mac, is_gateway in all_devices:
            device_id = cell_id
            label = f"{ip} - {mac}"

            mac_lower = mac.lower()
            if ip == current_interface:
                style = current_pc
            elif is_gateway:
                style = gateway_pc
            elif mac_lower == 'ff-ff-ff-ff-ff-ff' or mac_lower.startswith('01-00-5e'):
                style = broadcast_pc
            else:
                style = normal_pc

            x_pos = 600 + radius * math.cos(angle)
            y_pos = 400 + radius * math.sin(angle)

            xml_header += (
                f'        <mxCell id="{device_id}" value="{label}" style="{style}" vertex="1" parent="1">\n'
                f'          <mxGeometry x="{x_pos}" y="{y_pos}" width="100" height="100" as="geometry"/>\n'
                f'        </mxCell>\n'
            )
            connections.append((center_id, device_id))
            cell_id += 1
            angle += angle_step

        for source, target in connections:
            xml_header += (
                f'        <mxCell id="{cell_id}" edge="1" parent="1" source="{source}" target="{target}" style="endArrow=block;strokeColor=#000000;">\n'
                f'          <mxGeometry relative="1" as="geometry"/>\n'
                f'        </mxCell>\n'
            )
            cell_id += 1

        xml_footer = (
            '      </root>\n'
            '    </mxGraphModel>\n'
            '  </diagram>\n'
            '</mxfile>'
        )

        with open(filename, "w") as f:
            f.write(xml_header + xml_footer)
        print(f"Network diagram saved as {filename}")

    def main(self) -> None:
        all_arps = self.get_all_arp_entries()
        self.parse_arp_entries(all_arps)
        print(f'Final entries dict is: {self.arp_entries}')
        self.generate_drawio("network_map.drawio")


if __name__ == '__main__':
    network_mapper = NetworkMapper()
    network_mapper.main()
