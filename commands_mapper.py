cmd_map = {
    "Linux": {
        "get_arps": ["cat", "/proc/net/arp"],
        "parser_function": "linux_parser",
        "pinger": ["ping", "-c", "2"]

    },
    "Windows": {
        "get_arps": ["arp", "-a"],
        "parser_function": "windows_parser",
        "pinger": ["ping", "-n", "2"]
    }
}
