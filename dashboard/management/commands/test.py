with open('data/list_jy.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f]
# list = lines.remove('')
clean_list = list(filter(None, lines))
print(clean_list)

print(len(clean_list))
print(clean_list[80])