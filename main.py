import random
import tensorflow as tf
import numpy as np
import re


f = open("data/data.txt")
words = []
wrd2idx = {}
def text2words(text):
    text = (text.replace("\n"," "))
    text = ((text.replace("]","").replace(",","").replace("[","").replace("`","").replace("\"","").replace("\\","").replace("/","").replace("\'","").replace("  "," ").lower()))
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
    for word in text2words(l):
        if word.count(" ") != len(word):
            if not word in words:
                words.append(word)
                wrd2idx[word] = i
                i+=1
    l = f.readline()
f.close()


f = open("data/data.txt")
text = f.read()
idx2wrd = np.array(words)

data = [[x[0],x[1]] for x in re.findall(r"\[\[([^\]]+)\]([^\]]+)\]",text)]


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


import tensorflow as tf

import numpy as np
import os
import time

tf.enable_eager_execution()

examples_per_epoch = 200
text_as_int = np.array([wrd2idx[w] for w in text2words(text)])

# Create training examples / targets
wrd_dataset = tf.data.Dataset.from_tensor_slices(text_as_int)

for i in wrd_dataset.take(5):
  print(idx2wrd[i.numpy()])

sequences = char_dataset.batch(, drop_remainder=True)
