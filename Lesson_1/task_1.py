word_list = ["разработка", "сокет", "декоратор"]

def words_check(words):
	for i in words:
		print(i)
		print(type(i))
	print()

words_check(word_list)

for i in range(len(word_list)):
	word_list[i] = word_list[i].encode("unicode-escape").decode("utf-8")

words_check(word_list)
