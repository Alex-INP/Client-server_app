import yaml

data = {"key_1": ["word_1", "word_2"], "key_2": 2, "key_3": {"k_1": "25\u20ac", "k_2": "54\u20ac", "k_3": "77\u20ac"}}

with open("final_file.yaml", "w", encoding="utf-8") as file:
	yaml.dump(data, file, default_flow_style=False, allow_unicode = True)

with open("final_file.yaml", "r", encoding="utf-8") as file:
	content = yaml.load(file, yaml.Loader)
	if data == content:
		print("Equal")
