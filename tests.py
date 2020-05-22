f = open("data/data.txt")
dwords = {}
l = f.readline()
while l:
    for word in (l.replace("]","").replace(",","").replace("\n"," ").replace("[","").replace("`","").replace("\"","").replace("\\","").replace("/","").replace("\'","").lower()).split(" "):
        if word.count(" ") != len(word):
            try:
                dwords[word]+=1
            except:
                dwords[word]=1
    l = f.readline()


def merge_sort(sort_list):
    if len(sort_list) > 1:
        mid = len(sort_list) // 2
        leftHalf = sort_list[:mid]
        rightHalf = sort_list[mid:]

        merge_sort(leftHalf)
        merge_sort(rightHalf)

        i = 0
        j = 0
        k = 0
        while i < len(leftHalf) and j < len(rightHalf):
            if leftHalf[i][1] < rightHalf[j][1]:
                sort_list[k] = leftHalf[i]
                i = i + 1
            else:
                sort_list[k] = rightHalf[j]
                j = j + 1
            k = k + 1

        while i < len(leftHalf):
            sort_list[k] = leftHalf[i]
            i = i + 1
            k = k + 1

        while j < len(rightHalf):
            sort_list[k] = rightHalf[j]
            j = j + 1
            k = k + 1

words = []

for word,num in dwords.items():
    words.append([word,num])
print(dwords["xdxd"])
merge_sort(words)
print([w[0] for w in words[:200]])
f.close()