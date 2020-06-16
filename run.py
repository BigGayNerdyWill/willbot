
import tensorflow as tf
import tensorflow_datasets as tfds

import os
import re
import numpy as np
import time
import matplotlib.pyplot as plt
import sys
sent  = 0

messgaes = {}

# Maximum number of samples to preprocess
MAX_SAMPLES = 1000000

def preprocess_sentence(sentence):
	sentence = sentence.lower().strip()
	# creating a space between a word and the punctuation following it
	# eg: "he is a boy." => "he is a boy ."
	sentence = re.sub(r"([?.!,])", r" \1 ", sentence)
	sentence = re.sub(r'[" "]+', " ", sentence)
	# replacing everything with space except (a-z, A-Z, ".", "?", "!", ",")
	sentence = re.sub(r"['`]+","",sentence)
	sentence = re.sub(r"[^a-zA-Z?.!,]+", " ", sentence)
	sentence = sentence.strip()
	# adding a start and an end token to the sentence
	return sentence




#questions = questions[:1024]
#answers = answers[:1024]
# Build tokenizer using tfds for both questions and answers
tokenizer = tfds.features.text.SubwordTextEncoder.load_from_file("training_1/tokens")
print("tokenizer made")
# Define start and end token to indicate the start and end of a sentence
START_TOKEN, END_TOKEN = [tokenizer.vocab_size], [tokenizer.vocab_size + 1]

# Vocabulary size plus start and end token
VOCAB_SIZE = tokenizer.vocab_size + 2

MAX_LENGTH = 40

questions = []
answers = []
#print("\n".join(["{0}: question: \"{1}\" , answer: \"{2}\"".format(x,questions[x],answers[x]) for x in range(10)]))
# Tokenize, filter and pad sentences
def tokenize_and_filter(inputs, outputs):
    tokenized_inputs, tokenized_outputs = [], []
    
    for (sentence1, sentence2) in zip(inputs, outputs):
        # tokenize sentence
        sentence1 = START_TOKEN + tokenizer.encode(sentence1) + END_TOKEN
        sentence2 = START_TOKEN + tokenizer.encode(sentence2) + END_TOKEN
        # check tokenized sentence max length
        if len(sentence1) <= MAX_LENGTH and len(sentence2) <= MAX_LENGTH:
            tokenized_inputs.append(sentence1)
            tokenized_outputs.append(sentence2)
    
    # pad tokenized sentences
    tokenized_inputs = tf.keras.preprocessing.sequence.pad_sequences(
            tokenized_inputs, maxlen=MAX_LENGTH, padding='post')
    tokenized_outputs = tf.keras.preprocessing.sequence.pad_sequences(
            tokenized_outputs, maxlen=MAX_LENGTH, padding='post')
    
    return tokenized_inputs, tokenized_outputs


questions, answers = tokenize_and_filter(questions, answers)

print('Vocab size: {}'.format(VOCAB_SIZE))
print('Number of samples: {}'.format(len(questions)))
BATCH_SIZE = 512
BUFFER_SIZE = 20000

# decoder inputs use the previous target as input
# remove START_TOKEN from targets
dataset = tf.data.Dataset.from_tensor_slices((
        {
                'inputs': questions,
                'dec_inputs': answers[:, :-1]
        },
        {
                'outputs': answers[:, 1:]
        },
))

dataset = dataset.cache()
dataset = dataset.shuffle(BUFFER_SIZE)
dataset = dataset.batch(BATCH_SIZE)
dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)



def scaled_dot_product_attention(query, key, value, mask):
    """Calculate the attention weights. """
    matmul_qk = tf.matmul(query, key, transpose_b=True)

    # scale matmul_qk
    depth = tf.cast(tf.shape(key)[-1], tf.float32)
    logits = matmul_qk / tf.math.sqrt(depth)

    # add the mask to zero out padding tokens
    if mask is not None:
        logits += (mask * -1e9)

    # softmax is normalized on the last axis (seq_len_k)
    attention_weights = tf.nn.softmax(logits, axis=-1)

    output = tf.matmul(attention_weights, value)

    return output

class MultiHeadAttention(tf.keras.layers.Layer):

    def __init__(self, d_model, num_heads, name="multi_head_attention"):
        super(MultiHeadAttention, self).__init__(name=name)
        self.num_heads = num_heads
        self.d_model = d_model

        assert d_model % self.num_heads == 0

        self.depth = d_model // self.num_heads

        self.query_dense = tf.keras.layers.Dense(units=d_model)
        self.key_dense = tf.keras.layers.Dense(units=d_model)
        self.value_dense = tf.keras.layers.Dense(units=d_model)

        self.dense = tf.keras.layers.Dense(units=d_model)

    def split_heads(self, inputs, batch_size):
        inputs = tf.reshape(
                inputs, shape=(batch_size, -1, self.num_heads, self.depth))
        return tf.transpose(inputs, perm=[0, 2, 1, 3])

    def call(self, inputs):
        query, key, value, mask = inputs['query'], inputs['key'], inputs[
                'value'], inputs['mask']
        batch_size = tf.shape(query)[0]

        # linear layers
        query = self.query_dense(query)
        key = self.key_dense(key)
        value = self.value_dense(value)

        # split heads
        query = self.split_heads(query, batch_size)
        key = self.split_heads(key, batch_size)
        value = self.split_heads(value, batch_size)

        # scaled dot-product attention
        scaled_attention = scaled_dot_product_attention(query, key, value, mask)

        scaled_attention = tf.transpose(scaled_attention, perm=[0, 2, 1, 3])

        # concatenation of heads
        concat_attention = tf.reshape(scaled_attention,
                                                                    (batch_size, -1, self.d_model))

        # final linear layer
        outputs = self.dense(concat_attention)

        return outputs

def create_padding_mask(x):
  mask = tf.cast(tf.math.equal(x, 0), tf.float32)
  # (batch_size, 1, 1, sequence length)
  return mask[:, tf.newaxis, tf.newaxis, :]

def create_look_ahead_mask(x):
    seq_len = tf.shape(x)[1]
    look_ahead_mask = 1 - tf.linalg.band_part(tf.ones((seq_len, seq_len)), -1, 0)
    padding_mask = create_padding_mask(x)
    return tf.maximum(look_ahead_mask, padding_mask)

class PositionalEncoding(tf.keras.layers.Layer):

    def __init__(self, position, d_model):
        super(PositionalEncoding, self).__init__()
        self.pos_encoding = self.positional_encoding(position, d_model)

    def get_angles(self, position, i, d_model):
        angles = 1 / tf.pow(10000, (2 * (i // 2)) / tf.cast(d_model, tf.float32))
        return position * angles

    def positional_encoding(self, position, d_model):
        angle_rads = self.get_angles(
                position=tf.range(position, dtype=tf.float32)[:, tf.newaxis],
                i=tf.range(d_model, dtype=tf.float32)[tf.newaxis, :],
                d_model=d_model)
        # apply sin to even index in the array
        sines = tf.math.sin(angle_rads[:, 0::2])
        # apply cos to odd index in the array
        cosines = tf.math.cos(angle_rads[:, 1::2])

        pos_encoding = tf.concat([sines, cosines], axis=-1)
        pos_encoding = pos_encoding[tf.newaxis, ...]
        return tf.cast(pos_encoding, tf.float32)

    def call(self, inputs):
        return inputs + self.pos_encoding[:, :tf.shape(inputs)[1], :]



def encoder_layer(units, d_model, num_heads, dropout, name="encoder_layer"):
  inputs = tf.keras.Input(shape=(None, d_model), name="inputs")
  padding_mask = tf.keras.Input(shape=(1, 1, None), name="padding_mask")

  attention = MultiHeadAttention(
      d_model, num_heads, name="attention")({
          'query': inputs,
          'key': inputs,
          'value': inputs,
          'mask': padding_mask
      })
  attention = tf.keras.layers.Dropout(rate=dropout)(attention)
  attention = tf.keras.layers.LayerNormalization(
      epsilon=1e-6)(inputs + attention)

  outputs = tf.keras.layers.Dense(units=units, activation='relu')(attention)
  outputs = tf.keras.layers.Dense(units=d_model)(outputs)
  outputs = tf.keras.layers.Dropout(rate=dropout)(outputs)
  outputs = tf.keras.layers.LayerNormalization(
      epsilon=1e-6)(attention + outputs)

  return tf.keras.Model(
      inputs=[inputs, padding_mask], outputs=outputs, name=name)



def encoder(vocab_size,
                        num_layers,
                        units,
                        d_model,
                        num_heads,
                        dropout,
                        name="encoder"):
    inputs = tf.keras.Input(shape=(None,), name="inputs")
    padding_mask = tf.keras.Input(shape=(1, 1, None), name="padding_mask")

    embeddings = tf.keras.layers.Embedding(vocab_size, d_model)(inputs)
    embeddings *= tf.math.sqrt(tf.cast(d_model, tf.float32))
    embeddings = PositionalEncoding(vocab_size, d_model)(embeddings)

    outputs = tf.keras.layers.Dropout(rate=dropout)(embeddings)

    for i in range(num_layers):
        outputs = encoder_layer(
                units=units,
                d_model=d_model,
                num_heads=num_heads,
                dropout=dropout,
                name="encoder_layer_{}".format(i),
        )([outputs, padding_mask])

    return tf.keras.Model(
            inputs=[inputs, padding_mask], outputs=outputs, name=name)

def decoder_layer(units, d_model, num_heads, dropout, name="decoder_layer"):
    inputs = tf.keras.Input(shape=(None, d_model), name="inputs")
    enc_outputs = tf.keras.Input(shape=(None, d_model), name="encoder_outputs")
    look_ahead_mask = tf.keras.Input(
            shape=(1, None, None), name="look_ahead_mask")
    padding_mask = tf.keras.Input(shape=(1, 1, None), name='padding_mask')

    attention1 = MultiHeadAttention(
            d_model, num_heads, name="attention_1")(inputs={
                    'query': inputs,
                    'key': inputs,
                    'value': inputs,
                    'mask': look_ahead_mask
            })
    attention1 = tf.keras.layers.LayerNormalization(
            epsilon=1e-6)(attention1 + inputs)

    attention2 = MultiHeadAttention(
            d_model, num_heads, name="attention_2")(inputs={
                    'query': attention1,
                    'key': enc_outputs,
                    'value': enc_outputs,
                    'mask': padding_mask
            })
    attention2 = tf.keras.layers.Dropout(rate=dropout)(attention2)
    attention2 = tf.keras.layers.LayerNormalization(
            epsilon=1e-6)(attention2 + attention1)

    outputs = tf.keras.layers.Dense(units=units, activation='relu')(attention2)
    outputs = tf.keras.layers.Dense(units=d_model)(outputs)
    outputs = tf.keras.layers.Dropout(rate=dropout)(outputs)
    outputs = tf.keras.layers.LayerNormalization(
            epsilon=1e-6)(outputs + attention2)

    return tf.keras.Model(
            inputs=[inputs, enc_outputs, look_ahead_mask, padding_mask],
            outputs=outputs,
            name=name)

def decoder(vocab_size,
                        num_layers,
                        units,
                        d_model,
                        num_heads,
                        dropout,
                        name='decoder'):
    inputs = tf.keras.Input(shape=(None,), name='inputs')
    enc_outputs = tf.keras.Input(shape=(None, d_model), name='encoder_outputs')
    look_ahead_mask = tf.keras.Input(
            shape=(1, None, None), name='look_ahead_mask')
    padding_mask = tf.keras.Input(shape=(1, 1, None), name='padding_mask')
    
    embeddings = tf.keras.layers.Embedding(vocab_size, d_model)(inputs)
    embeddings *= tf.math.sqrt(tf.cast(d_model, tf.float32))
    embeddings = PositionalEncoding(vocab_size, d_model)(embeddings)

    outputs = tf.keras.layers.Dropout(rate=dropout)(embeddings)

    for i in range(num_layers):
        outputs = decoder_layer(
                units=units,
                d_model=d_model,
                num_heads=num_heads,
                dropout=dropout,
                name='decoder_layer_{}'.format(i),
        )(inputs=[outputs, enc_outputs, look_ahead_mask, padding_mask])

    return tf.keras.Model(
            inputs=[inputs, enc_outputs, look_ahead_mask, padding_mask],
            outputs=outputs,
            name=name)


def transformer(vocab_size,
                                num_layers,
                                units,
                                d_model,
                                num_heads,
                                dropout,
                                name="transformer"):
    inputs = tf.keras.Input(shape=(None,), name="inputs")
    dec_inputs = tf.keras.Input(shape=(None,), name="dec_inputs")

    enc_padding_mask = tf.keras.layers.Lambda(
            create_padding_mask, output_shape=(1, 1, None),
            name='enc_padding_mask')(inputs)
    # mask the future tokens for decoder inputs at the 1st attention block
    look_ahead_mask = tf.keras.layers.Lambda(
            create_look_ahead_mask,
            output_shape=(1, None, None),
            name='look_ahead_mask')(dec_inputs)
    # mask the encoder outputs for the 2nd attention block
    dec_padding_mask = tf.keras.layers.Lambda(
            create_padding_mask, output_shape=(1, 1, None),
            name='dec_padding_mask')(inputs)

    enc_outputs = encoder(
            vocab_size=vocab_size,
            num_layers=num_layers,
            units=units,
            d_model=d_model,
            num_heads=num_heads,
            dropout=dropout,
    )(inputs=[inputs, enc_padding_mask])

    dec_outputs = decoder(
            vocab_size=vocab_size,
            num_layers=num_layers,
            units=units,
            d_model=d_model,
            num_heads=num_heads,
            dropout=dropout,
    )(inputs=[dec_inputs, enc_outputs, look_ahead_mask, dec_padding_mask])

    outputs = tf.keras.layers.Dense(units=vocab_size, name="outputs")(dec_outputs)

    return tf.keras.Model(inputs=[inputs, dec_inputs], outputs=outputs, name=name)



tf.keras.backend.clear_session()

# Hyper-parameters
NUM_LAYERS = 4
D_MODEL = 512
NUM_HEADS = 8
UNITS = 2048
DROPOUT = 0.1
EPOCHS = 10


model = transformer(
    vocab_size=VOCAB_SIZE,
    num_layers=NUM_LAYERS,
    units=UNITS,
    d_model=D_MODEL,
    num_heads=NUM_HEADS,
    dropout=DROPOUT)

model = model

checkpoint_path = "training_1/cp.ckpt"
checkpoint_dir = os.path.dirname(checkpoint_path)

model.load_weights(checkpoint_path)


def loss_function(y_true, y_pred):
  y_true = tf.reshape(y_true, shape=(-1, MAX_LENGTH - 1))
  
  loss = tf.keras.losses.SparseCategoricalCrossentropy(
      from_logits=True, reduction='none')(y_true, y_pred)

  mask = tf.cast(tf.not_equal(y_true, 0), tf.float32)
  loss = tf.multiply(loss, mask)

  return tf.reduce_mean(loss)



class CustomSchedule(tf.keras.optimizers.schedules.LearningRateSchedule):

  def __init__(self, d_model, warmup_steps=4000):
    super(CustomSchedule, self).__init__()

    self.d_model = d_model
    self.d_model = tf.cast(self.d_model, tf.float32)

    self.warmup_steps = warmup_steps

  def __call__(self, step):
    arg1 = tf.math.rsqrt(step)
    arg2 = step * (self.warmup_steps**-1.5)

    return tf.math.rsqrt(self.d_model) * tf.math.minimum(arg1, arg2)

learning_rate = CustomSchedule(D_MODEL)

optimizer = tf.keras.optimizers.Adam(
    learning_rate, beta_1=0.9, beta_2=0.98, epsilon=1e-9)

def accuracy(y_true, y_pred):
  # ensure labels have shape (batch_size, MAX_LENGTH - 1)
  y_true = tf.reshape(y_true, shape=(-1, MAX_LENGTH - 1))
  return tf.keras.metrics.sparse_categorical_accuracy(y_true, y_pred)

model.compile(optimizer=optimizer, loss=loss_function, metrics=[accuracy])

# Create a callback that saves the model's weights
cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path,
                                                 save_weights_only=True,
                                                 verbose=1)

#model.fit(dataset, epochs=EPOCHS,callbacks=[cp_callback])




def evaluate(sentence):
  sentence = preprocess_sentence(sentence)

  sentence = tf.expand_dims(
      START_TOKEN + tokenizer.encode(sentence) + END_TOKEN, axis=0)

  output = tf.expand_dims(START_TOKEN, 0)

  for i in range(MAX_LENGTH):
    predictions = model(inputs=[sentence, output], training=False)

    # select the last word from the seq_len dimension
    predictions = predictions[:, -1:, :]
    predicted_id = tf.cast(tf.argmax(predictions, axis=-1), tf.int32)

    # return the result if the predicted_id is equal to the end token
    if tf.equal(predicted_id, END_TOKEN[0]):
      break

    # concatenated the predicted_id to the output which is given to the decoder
    # as its input.
    output = tf.concat([output, predicted_id], axis=-1)

  return tf.squeeze(output, axis=0)


def predict(sentence):
  prediction = evaluate(sentence)

  predicted_sentence = tokenizer.decode(
      [i for i in prediction if i < tokenizer.vocab_size])

  print('Input: {}'.format(sentence))
  print('Output: {}'.format(predicted_sentence))

  return predicted_sentence



import discord,random,re,datetime
WToxen = "NDcxNjgwMzIxNDE1NDEzNzYx.XsXIog.bVtw0uVFw34TLrnEeVOiGNE3X_s"
W2Tokex = "NjkzOTY4MzM0MzI4Mjk5NTIw.XuUTiw.5fKoUCgoc8foLnhSp9fAz7uqvkE"
TOKEN = 'NzA4MDQ0MTEyMDkxMjgzNDk2.XrS0qw.4Ck99so3nWvwiENZ58nvjguPmyY'
client = discord.Client()



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
                break
    msg = ' '.join(text)
    for word in text:
        if "<" in word or ">" in word:
            msg.replace(word+" ","")
            msg.replace(" "+word,"")
            msg.replace(word,"")
        if "http" in word or "www" in word:
            msg.replace(word,"link")
    
    return msg
  
rndbol = False

async def sendmsg(channel,msg):
    async with channel.typing():
        start = time.process_time()
        msg = predict(msg)
        t= time.process_time() - start
        await asyncio.sleep(int(abs(round(int(len(msg)/50)) - t)))
        await channel.send(msg)

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user or message.author.bot:
        return
    
    try:
        cnam = message.channel.name
        if "bot" in cnam or "vent" in cnam or "tw" in cnam or "nsfw" in cnam or "trigger" in cnam or message.channel.is_nsfw() or "rant" in cnam:
            return
    except:
        True
    global rndbol

    

    if isinstance(message.channel, discord.DMChannel):
        rndbol = rndbol or (round(random.randrange(0,2)))==1
        if not rndbol:
            try:
                messgaes[message.author.id]+=1
            except:
                messgaes[message.author.id] = 1
            
            if messgaes[message.author.id] > 3:
                rndbol = True

        if rndbol:
            messgaes[message.author.id] = 0
    
    elif isinstance(message.channel, discord.TextChannel):
        rndbol = rndbol or (random.randrange(0,10)==1)
    else:
        rndbol = False



    if (rndbol and "<" not in message.content and ">" not in message.content and "www" not in message.content and "http" not in message.content):
        text = ""
        chnl = message.channel
        async for msg in chnl.history(limit=5,oldest_first=False):
            text = " " + text2words(msg.content) + text
        
        text = text[1:]

        
        try:
            rndbol = False
            await sendmsg(chnl,text)
            #print("{0} > {1}".format(text,output))
            global sent
            sent +=1
        except:
            print(message.guild.name)

        
def strToBool(str):
    return str=="True" or str=="true"

@client.event
async def on_connect():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


async def startclient(will,alt):
    if will:
        if alt:
            await client.login(W2Tokex,bot=False)
        else:
            await client.login(WToxen,bot=False)

    else:
        await client.login(TOKEN)
    print("logged in")
    await client.connect()
    print("connected")



import asyncio
print(sys.argv)
loop = asyncio.get_event_loop()
try:
    bols = [strToBool(x) for x in sys.argv[1:3]]
    print(bols)
    try:
        loop.run_until_complete(startclient(bols[0],bols[1]))
    finally:
        loop.close()
except:
    print("Must give two boolean inputs")
    quit()
