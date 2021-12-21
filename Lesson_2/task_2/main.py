import json


def write_order_to_json(item, quantity, price, buyer, date):
	new_dict = {
		"item": item,
		"quantity": quantity,
		"price": price,
		"buyer": buyer,
		"date": date
	}
	with open("orders.json", "r+", encoding="utf-8") as file:
		data = json.load(file)
		file.seek(0)
		data["orders"].append(new_dict)
		json.dump(data, file, indent=4, ensure_ascii=False)

write_order_to_json("pen", 20, 200, "oleg", "23.12.2000")
write_order_to_json("pencil", 23, 150, "dmitriy", "23.13.2005")
write_order_to_json("book", 20, 200, "vasiliy", "02.03.2007")
write_order_to_json("тетрадь", 20, 200, "eugeni", "18.10.2008")
write_order_to_json("стол", 20, 200, "larisa", "20.07.2009")
