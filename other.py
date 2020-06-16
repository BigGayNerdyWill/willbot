import re
f = open("trainingdata/data.txt")
o= open("trainingdata/data2.txt",'w')
l=f.readline()


def text2words(text):
    text = (text.replace("\n"," ").replace("\t"," "))
    text = ((text.replace("]","").replace("*","").replace("~","").replace(",","").replace("[","").replace("`","").replace("\"","").replace("\\","").replace("/","").replace("\'","").replace("  "," ").lower()))
    while "  " in text:
        text = text.replace("  "," ")
    text = text.split(" ")
    a = True
    while True:
        try:
            if a:
                text.remove(" ")
            else:
                text.remove("")
        except:
            if a:
                a =False
                continue
            else:
                return text
   
i=0
out = ""
words = {}
while l and i<i+1:
    if len(l)<=500:
        try:
            for x in re.findall(r"\[+\[+([^\]]+)\]+ ([^\]][^\]]+)\]+",l)[0]:
                lineout = ""
                for word in text2words(x):
                    if "2" in word and not " 2 " in word and "24" not in word:
                        word = word.replace("2","s")
                    if "ii" in word:
                        word = word.replace("ii","i")
                    if word.count(" ") != len(word) and ">" not in word and "<" not in word:
                        lineout = lineout + (" " + word)
                        try:
                            if not words[word]:
                                words[word] = True
                        except:
                            words[word] = False
                out = out + lineout[1:] + ("\n")
            i+=1
        except:
            i=i
    l = f.readline()

try:
    if not words["link"]:
        words["link"] = True
except:
    words["link"] = False

for word,bol in words.items():
    if "http" in word or "www" in word:
        out = out.replace(word,"link")
        words.remove(word)
        #print(word)
        #print(word in out)


print(len)
o.write(out)



