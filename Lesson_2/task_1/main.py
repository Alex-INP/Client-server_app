import re
import csv


def get_data():
	filenames = ["info_1.txt", "info_2.txt", "info_3.txt"]
	main_data = [["Изготовитель системы", "Название ОС", "Код продукта", "Тип системы"]]
	ind = 1
	for i in filenames:
		with open(i, "r", encoding="utf-8") as file:
			content = file.read()

			sys_manufacturer = re.search(re.compile(r'(?<=Изготовитель системы:\s{13}).+'), content).group()
			os_name = re.search(re.compile(r'(?<=Название ОС:\s{22}).+'), content).group()
			product_code = re.search(re.compile(r'(?<=Код продукта:\s{21}).+'), content).group()
			system_type = re.search(re.compile(r'(?<=Тип системы:\s{22}).+'), content).group()

			main_data.append([ind, sys_manufacturer, os_name, product_code, system_type])
			ind += 1
	return main_data

def write_to_csv(file_link):
	data = get_data()
	with open(file_link, "w", encoding="utf-8") as file:
		writer = csv.writer(file)
		for i in data:
			if type(i[0]) == int:
				writer.writerow(i)
			else:
				writer.writerow(i)
				file.seek(file.tell()-2, 0)

write_to_csv("final_file.csv")
