"""
@Author: Preslav Iliev
"""
import subprocess
import platform
import commands_mapper




class NetworkMapper:
    def __init__(self) -> None:
        self.arp_entries = {}

    @staticmethod
    def get_os_name() -> str:
        """
        :return: Windows or Linux as a string
        """
        return platform.system()  # Tested on Linux (debian Distributions) and Windows

    def get_all_arp_entries(self, os_name: str) -> str or Exception:
        try:
            return subprocess.run(commands_mapper.cmd_map[os_name]['get_arps'], stderr=subprocess.PIPE, text=True).stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e}"

    def main(self) -> None:
        self.get_all_arp_entries(self.get_os_name())




if __name__ == '__main__':
    network_mapper = NetworkMapper()
    network_mapper.main()
