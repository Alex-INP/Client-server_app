import tabulate
from Task_2 import host_range_ping

def host_range_ping_tab(addr, delta):
	print(tabulate.tabulate(host_range_ping(addr, delta), headers="keys", tablefmt="grid", stralign="center"))

if __name__ == "__main__":
	host_range_ping_tab("192.168.0.1", 3)


