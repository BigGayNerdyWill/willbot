import random
import tensorflow as tf
import numpy as np
import re
from keras.preprocessing import sequence

regex = r"\[+\[+([^\]]+)\]+([^\]]+)\]+"
regex = r"([^\t]*)\t([^\t]*)"

f = open("data/data2.txt")
words = set()
wrd2idx = {}
def text2words(text):
    text = (text.replace("\n"," "))
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
l = f.readline()
while l:
    for x in re.findall(regex,l)[0]:
        for word in text2words(x):
            if word.count(" ") != len(word) and word != "":
                if not word in words:
                    words.add(word)
                    wrd2idx[word] = i
                    i+=1
    l = f.readline()
f.close()

input_token_index = dict(
    [(char, i) for i, char in enumerate(words)])

quit()
f = open("data/data.txt")
text = f.read()
idx2wrd = np.array(words)

data = [[x[0],x[1]] for x in re.findall(regex,text)]


def sigmoid(nump):
    return 1/(1+np.exp(-nump))

def sigmoidGradient(z):
    return sigmoid(z) * (1 - sigmoid(z))

def lstm_cell_forward(Slt,Alt,Xt,Wf,bf,Wu,bu,Ws,bs,Wo,bo):

    concat = np.concatenate((Alt,Xt),axis=0)
    St_temp = np.tanh(np.dot(Ws,concat) + bs) 
    Fu = sigmoid(np.dot(Wu,concat) + bu)
    Ff = sigmoid(np.dot(Wf,concat) + bf)
    Fo = sigmoid(np.dot(Wo,concat) + bo)

    St = Fi*St_temp + Ff * Slt
    At - Fo * np.tanh(St)

    return [Ct_temp,Fu,Ff,Fo,Ct,At]


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

'''
import tensorflow as tf
import numpy as np
import os
import time

emb_size = 64
hidden_units = 32
weight_len = 128


tf.enable_eager_execution()
maxlen = 0
X=[]
Y=[]
examples_per_epoch = 200
for x in range(len(data)):
    x1 = [wrd2idx[w] for w in text2words(data[x][0])]
    x2 = [wrd2idx[w] for w in text2words(data[x][1])]
    x1.append(i)
    x2.append(i)
    maxlen = len(x2) if len(x2)>maxlen 
    maxlen = len(x1) if len(x1)>maxlen 
    #v=x1
    #v.append(i)
    #for a in x2:
    #    v.append(a)
    #v.append(i+1)
    X.append(x1)
    Y.append(x2)

# Create training examples / targets
darray = np.array(data)
#dataset = sequence.pad_sequences(np.array(data), padding='post')

sentance = tf.placeholder(tf.int32.[1,maxlen])
'''