# NeuralModels
A library for Recurrent Neural Networks built on top of Theano. It allows quick prototyping of complicated structures of Recurrent Neural Networks. Checkout some of the existing architectures (and research papers) implemented using NeuralModels https://github.com/asheshjain399/RNNexp/

## INSTALL

python setup.py develop

In order to check NeuralModels is correctly installed, try the character-rnn example. 
``` 
python char-rnn.py 
```

## Description

neuralmodels: Python module containing definition of layers, optimization methods, and few models. 

## Models

NeuralModels comes with some pre-implemented models in the models directory

```
models/DRA.py
``` 
is the structural-RNN (S-RNN) code for doing deep learning on spatio-temporal graphs. The paper is present here http://www.cs.stanford.edu/people/ashesh/srnn See the repository https://github.com/asheshjain399/RNNexp/ for examples to use S-RNN

```
models/RNN.py
```
This is a simple RNN implementation.

In order to implement strucutures of RNN see examples such as models/SharedRNN.py

## Layers

Many standard layers are pre-implemented in NeuralModels:

```
layers/LSTM.py
```
implements the standard LSTM with gradient clipping (tune-able parameters)

```
layers/multilayerLSTM.py
```
Use this to create a stack of LSTM with skip-input and output connections. If skip-input and output connections are not desired, then simply create an array of layers/LSTM.py
```
layers/simpleRNN.py
```
implements the Recurrent Neural Network
```
layers/softmax.py
```
this is the softmax layer, or commonly the output layer of the architecture.
```
layers/OneHot.py
```
this layer generates the one-hot vector representation, this is commonly the input layer of the architecture when dealing with finite size vocabulary (eg. in NLP)
```
layers/TemporalInputFeatures.py
```
this is the input layer of the architecture when we have precomputed feature vectors. The shape of input is:
```
T x N x D
```
T is the number of time-steps
N is the number of sequences
D is the dimension of each feature vector

