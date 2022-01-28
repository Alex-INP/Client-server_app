import ipaddress
from Task_1 import host_ping

def host_range_ping(start_ip, delta):
	if int(str(start_ip).split(".")[-1]) == 255:
		return [start_ip]

	start_ip = ipaddress.ip_address(start_ip)
	result = [start_ip]
	for i in range(delta):
		start_ip += 1
		result.append(start_ip)
		if int(str(start_ip).split(".")[-1]) == 255:
			break
	return host_ping(result)


if __name__ == "__main__":
	print(host_range_ping("192.168.0.1", 5))
