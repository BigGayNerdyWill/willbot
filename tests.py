import random

count=0
vals = [0,0,0,0]
for i in range(100000):

    count +=1
    vals[random.randrange(0,3)]+=1

    if i% 100 ==0:
        print("{0} tests ran with a mean of {1}".format(count,str(vals)))