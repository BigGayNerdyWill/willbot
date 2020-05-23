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

#forward progagaion
def lstm_cell_forward(Slt,Alt,Xt,Wf,bf,Wu,bu,Ws,bs,Wo,bo):

    concat = np.concatenate((Alt,Xt),axis=0)
    St_temp = np.tanh(np.dot(Ws,concat) + bs) 
    Fu = sigmoid(np.dot(Wu,concat) + bu)
    Ff = sigmoid(np.dot(Wf,concat) + bf)
    Fo = sigmoid(np.dot(Wo,concat) + bo)

    St = Fi*St_temp + Ff * Slt
    At - Fo * np.tanh(St)

    return [Ct_temp,Fu,Ff,Fo,Ct,At]


def nearby_word(emb_mat,onehot,W,b):
    return sigmoid(np.dot(W,(np.dot(emb_mat,onehot))) + b)

#backward progagation

#learning