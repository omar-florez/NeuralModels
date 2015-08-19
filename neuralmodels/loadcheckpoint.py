import theano
import numpy as np
import cPickle
from theano import tensor as T 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import math
import pdb
import sys 
from neuralmodels.layers import *
from neuralmodels.models import *

def loadLayers(model,layers_to_load):
	for layer_name in layers_to_load:
		model['config'][layer_name] = [eval(layer['layer'])(**layer['config']) for layer in model['config'][layer_name]]
	return model

def CreateSaveableModel(model,layers_to_save):
	for layerName in layers_to_save:
		layer_configs = []
		for layer in getattr(model,layerName):
			layer_config = layer.settings
			layer_name = layer.__class__.__name__
			weights = [p.get_value() for p in layer.params]
			layer_config['weights'] = weights
			layer_configs.append({'layer':layer_name, 'config':layer_config})
		model.settings[layerName] = layer_configs
	
	return model

def load(path):
	model = cPickle.load(open(path))
	model_class = eval(model['model'])  #getattr(models, model['model'])
	layer_args = ['layers']
	model = loadLayers(model,layer_args)
	model = model_class(**model['config'])
	return model

def loadDRA(path):
	model = cPickle.load(open(path))
	model_class = eval(model['model'])  #getattr(models, model['model'])

	edgeRNNs = {}
	for k in model['config']['edgeRNNs'].keys():
		layerlist = model['config']['edgeRNNs'][k]
		edgeRNNs[k] = [eval(layer['layer'])(**layer['config']) for layer in layerlist]
	model['config']['edgeRNNs'] = edgeRNNs

	nodeRNNs = {}
	for k in model['config']['nodeRNNs'].keys():
		layerlist = model['config']['nodeRNNs'][k]
		nodeRNNs[k] = [eval(layer['layer'])(**layer['config']) for layer in layerlist]
	model['config']['nodeRNNs'] = nodeRNNs
	model = model_class(**model['config'])
	return model
	
def loadSharedRNNVectors(path):
	model = cPickle.load(open(path))
	model_class = eval(model['model']) #getattr(models, model['model'])
	layer_args = ['shared_layers','layer_1','layer_2','layer_1_output','layer_2_output']
	model = loadLayers(model,layer_args)
	model = model_class(**model['config'])
	return model

def loadSharedRNN(path):
	model = cPickle.load(open(path))
	model_class = eval(model['model']) #getattr(models, model['model'])
	layer_args = ['shared_layers','layer_1','layer_2']
	model = loadLayers(model,layer_args)
	model = model_class(**model['config'])
	return model

def loadSharedRNNOutput(path):
	model = cPickle.load(open(path))
	model_class = eval(model['model']) #getattr(models, model['model'])
	layer_args = ['shared_layers','layer_1','layer_2','layer_1_detection','layer_1_anticipation','layer_2_detection','layer_2_anticipation']
	model = loadLayers(model,layer_args)
	model = model_class(**model['config'])
	return model

def loadMultipleRNNsCombined(path):
	model = cPickle.load(open(path))
	model_class = eval(model['model']) #getattr(models, model['model'])

	temp_layer = []
	for rnn_layer in model['config']['rnn_layers']:
		temp_layer.append([eval(layer['layer'])(**layer['config']) for layer in rnn_layer])
	model['config']['rnn_layers'] = temp_layer
	layer_args = ['combined_layer']
	model = loadLayers(model,layer_args)
	model = model_class(**model['config'])
	return model

def save(model, path):
	sys.setrecursionlimit(10000)
	layer_args = ['layers']
	model = CreateSaveableModel(model,layer_args)
	serializable_model = {'model':model.__class__.__name__, 'config':model.settings}
	cPickle.dump(serializable_model, open(path, 'wb'))

def saveSharedRNNVectors(model, path):
	sys.setrecursionlimit(10000)
	layer_args = ['shared_layers','layer_1','layer_2','layer_1_output','layer_2_output']
	model = CreateSaveableModel(model,layer_args)
	serializable_model = {'model':model.__class__.__name__, 'config':model.settings}
	cPickle.dump(serializable_model, open(path, 'wb'))

def saveSharedRNN(model, path):
	sys.setrecursionlimit(10000)
	layer_args = ['shared_layers','layer_1','layer_2']
	model = CreateSaveableModel(model,layer_args)
	serializable_model = {'model':model.__class__.__name__, 'config':model.settings}
	cPickle.dump(serializable_model, open(path, 'wb'))

def saveDRA(model,path):
	sys.setrecursionlimit(10000)

	edgeRNNs = getattr(model,'edgeRNNs')
	edgeRNN_saver = {}
	for k in edgeRNNs.keys():
		layer_configs = []
		for layer in edgeRNNs[k]:
			layer_config = layer.settings
			layer_name = layer.__class__.__name__
			weights = [p.get_value() for p in layer.params]
			layer_config['weights'] = weights
			layer_configs.append({'layer':layer_name, 'config':layer_config})
		edgeRNN_saver[k] = layer_configs
	model.settings['edgeRNNs'] = edgeRNN_saver

	nodeRNNs = getattr(model,'nodeRNNs')
	nodeRNN_saver = {}
	for k in nodeRNNs.keys():
		layer_configs = []
		for layer in nodeRNNs[k]:
			layer_config = layer.settings
			layer_name = layer.__class__.__name__
			weights = [p.get_value() for p in layer.params]
			layer_config['weights'] = weights
			layer_configs.append({'layer':layer_name, 'config':layer_config})
		nodeRNN_saver[k] = layer_configs
	model.settings['nodeRNNs'] = nodeRNN_saver
	serializable_model = {'model':model.__class__.__name__, 'config':model.settings}
	cPickle.dump(serializable_model, open(path, 'wb'))

def saveSharedRNNOutput(model, path):
	sys.setrecursionlimit(10000)
	layer_args = ['shared_layers','layer_1','layer_2','layer_1_detection','layer_1_anticipation','layer_2_detection','layer_2_anticipation']
	model = CreateSaveableModel(model,layer_args)
	serializable_model = {'model':model.__class__.__name__, 'config':model.settings}
	cPickle.dump(serializable_model, open(path, 'wb'))

def saveMultipleRNNsCombined(model, path):
	sys.setrecursionlimit(10000)	
	model.settings['rnn_layers'] = []
	for layers in getattr(model,'rnn_layers'):
		layer_configs = []
		for layer in layers:
			layer_config = layer.settings
			layer_name = layer.__class__.__name__
			weights = [p.get_value() for p in layer.params]
			layer_config['weights'] = weights
			layer_configs.append({'layer':layer_name, 'config':layer_config})
		model.settings['rnn_layers'].append(layer_configs)

	layer_args = ['combined_layer']
	model = CreateSaveableModel(model,layer_args)
	serializable_model = {'model':model.__class__.__name__, 'config':model.settings}
	cPickle.dump(serializable_model, open(path, 'wb'))


def plot_loss(lossfile):
	f = open(lossfile,'r')
	lines = f.readlines()
	f.close()
	loss = [float(l.strip()) for l in lines]
	iterations = range(len(loss))
	plt.plot(iterations,loss)
	plt.show()
