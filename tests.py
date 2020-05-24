def split(data,splits):
    splits= [round(x*len(data)/100) for x in splits]
    j=0
    for i in range(len(splits)):
        j+=splits[i]
        splits[i] = j
    train = data[:splits[0]]
    test = data[splits[0]:splits[1]]
    dev = data[splits[1]:splits[2]]
    return {"train":train,"test":test,"dev":dev}

a=[x for x in range(137)]
a = split(a,[80,10,10])
for i,u in a.items():
    print("{0} : {1}, {2}".format(i,u,len(u)))
