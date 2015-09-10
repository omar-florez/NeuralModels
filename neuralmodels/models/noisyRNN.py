from headers import *

class noisyRNN(object):
	def __init__(self,layers,cost,Y,learning_rate,update_type=RMSprop(),clipnorm=0.0):
		self.settings = locals()
		del self.settings['self']
		self.layers = layers
		self.learning_rate = learning_rate
		self.clipnorm = clipnorm	
		self.std = T.scalar(dtype=theano.config.floatX)
		
		self.update_type = update_type
		self.update_type.lr = self.learning_rate
		self.update_type.clipnorm = self.clipnorm

		for i in range(1, len(layers)):
			layers[i].connect(layers[i-1])
			if layers[i].__class__.__name__ == 'AddNoiseToInput':
				layers[i].std = self.std

		self.X = layers[0].input
		self.Y_pr = layers[-1].output()
		self.Y = Y

		self.cost =  cost(self.Y_pr,self.Y)
	        self.params = []
		for l in self.layers:
	                if hasattr(l,'params'):
				self.params.extend(l.params)


		self.num_params = 0
		for par in self.params:
			val = par.get_value()
			temp = 1
			for i in range(val.ndim):
				temp *= val.shape[i]		
			self.num_params += temp

		print 'Number of parameters ',self.num_params
			
		[self.updates,self.grads] = self.update_type.get_updates(self.params,self.cost)
		self.train = theano.function([self.X,self.Y,self.learning_rate,self.std],self.cost,updates=self.updates,on_unused_input='warn')
		self.predict = theano.function([self.X,self.std],self.layers[-1].output(),on_unused_input='warn')
		self.prediction_loss = theano.function([self.X,self.Y,self.std],self.cost,on_unused_input='warn')

		self.norm = T.sqrt(sum([T.sum(g**2) for g in self.grads]))
		self.grad_norm = theano.function([self.X,self.Y,self.std],self.norm,on_unused_input='warn')

	def fitModel(self,trX,trY,snapshot_rate=1,path=None,epochs=30,batch_size=50,learning_rate=1e-3,
		learning_rate_decay=0.97,std=1e-5,decay_after=-1,trX_validation=None,trY_validation=None,
		trX_forecasting=None,trY_forecasting=None,rng=np.random.RandomState(1234567890),epoch_start=None,
		decay_type=None,decay_schedule=None,decay_rate_schedule=None,
		use_noise=False,noise_schedule=None,noise_rate_schedule=None):

		from neuralmodels.loadcheckpoint import save

		'''Saving first 5 training examples. This is for visualization of training error'''	
		training_trajectories = trX[:,:5,:]
		if path:
			fname = 'train_example'
			self.saveForecastedMotion(training_trajectories,path,fname)

		'''While calculating the loos we ignore these many initial time steps'''
		delta_t_ignore = 50
	
		'''If loading an existing model then some of the parameters needs to be restored'''
		epoch_count = 0
		validation_set = []
		loss_after_each_minibatch = []
		complete_logger = ''
		if epoch_start is not None:
			epoch_count = epoch_start
			if path:
				lines = open('{0}logfile'.format(path)).readlines()
				for i in range(epoch_count):
					line = lines[i]
					values = line.strip().split(',')
					print values
					if len(values) == 1:
						loss_after_each_minibatch.append(float(values[0]))
						validation_set.append(-1)
					elif len(values) == 2:
						loss_after_each_minibatch.append(float(values[0]))
						validation_set.append(float(values[1]))
				if os.path.exists('{0}complete_log'.format(path)):
					complete_logger = open('{0}complete_log'.format(path)).read()
					complete_logger = complete_logger[:epoch_count]

		N = trX.shape[1]
		outputDim = trY.ndim
		seq_length = trY.shape[0] - delta_t_ignore
		feature_dim = trY.shape[2]
		batches_in_one_epoch = int(np.ceil(N*1.0 / batch_size))
		numrange = np.arange(N)
		X = []
		Y = []

		Tvalidation = 0
		Dvalidation = 0
		if (trX_validation is not None):
			Tvalidation = trX_validation.shape[0] - delta_t_ignore
			Dvalidation = trX_validation.shape[2]

		print 'batches in one epoch ',batches_in_one_epoch
		for epoch in range(epoch_count,epochs):
			t0 = time.time()

			'''Learning rate decay.'''	
			if decay_type:
				if decay_type == 'continuous' and decay_after > 0 and epoch > decay_after:
					learning_rate *= learning_rate_decay
				elif decay_type == 'schedule':
					for i in range(len(decay_schedule)):
						if decay_schedule[i] > 0 and epoch > decay_schedule[i]:
							learning_rate *= decay_rate_schedule[i]
							decay_schedule[i] = -1

			'''Set noise level.'''	
			if use_noise:
				for i in range(len(noise_schedule)):
					if noise_schedule[i] > 0 and epoch > noise_schedule[i]:
						std = noise_rate_schedule[i]
						noise_schedule[i] = -1


			'''Permuting before mini-batch iteration'''
			shuffle_list = rng.permutation(numrange)
			trX = trX[:,shuffle_list,:]
			if outputDim == 2:
				trY = trY[:,shuffle_list]
			elif outputDim == 3:
				trY = trY[:,shuffle_list,:]

			for j in range(batches_in_one_epoch):
				X = trX[:,j*batch_size:min((j+1)*batch_size,N),:]
				if outputDim == 2:
					Y = trY[:,j*batch_size:min((j+1)*batch_size,N)]
				elif outputDim == 3:
					Y = trY[:,j*batch_size:min((j+1)*batch_size,N),:]
				
				'''One iteration of training'''
				loss = self.train(X,Y,learning_rate,std)
				g = self.grad_norm(X,Y,std)
				loss_after_each_minibatch.append(loss)
				validation_set.append(-1)

				termout = 'e={1} m={2} lr={5} g_l2={4} noise={7} loss={0} normalized={3} skel_err={6}'.format(loss,epoch,j,(loss*1.0/(seq_length*feature_dim)),g,learning_rate,np.sqrt(loss*1.0/seq_length),std)
				complete_logger += termout + '\n'
				print termout

			'''Computing error on validation set'''
			if (trX_validation is not None) and (trY_validation is not None):
				validation_error = self.prediction_loss(trX_validation,trY_validation,1e-5)
				validation_set[-1] = validation_error
				termout = 'Validation: loss={0} normalized={1} skel_err={2}'.format(validation_error,(validation_error*1.0/(Tvalidation*Dvalidation)),np.sqrt(validation_error*1.0/Tvalidation))
				complete_logger += termout + '\n'
				print termout


			'''Trajectory forecasting on validation set'''
			if (trX_forecasting is not None) and (trY_forecasting is not None) and path and epoch % snapshot_rate == 0:
				forecasted_motion = self.predict_sequence(trX_forecasting,sequence_length=trY_forecasting.shape[0])
				fname = 'forecast_epoch_{0}'.format(epoch)
				self.saveForecastedMotion(forecasted_motion,path,fname)


			'''Saving the learned model so far'''
			if path:
				if epoch % snapshot_rate == 0:
					print 'saving snapshot checkpoint.{0}'.format(epoch)
					save(self,"{0}checkpoint.{1}".format(path,epoch))

				'''Writing training error and validation error in a log file'''
				f = open('{0}logfile'.format(path),'w')
				for l,v in zip(loss_after_each_minibatch,validation_set):
					if v > 0:
						f.write('{0},{1}\n'.format(l,v))
					else:
						f.write('{0}\n'.format(l))
				f.close()
				f = open('{0}complete_log'.format(path),'w')
				f.write(complete_logger)
				f.close()

				'''Get error on training trajectories'''
				training_prediction = self.predict(training_trajectories,1e-5)
				fname = 'train_error_epoch_{0}'.format(epoch)
				self.saveForecastedMotion(training_prediction,path,fname)

			t1 = time.time()
			termout = 'Epoch took {0} seconds'.format(t1-t0)
			complete_logger += termout + '\n'
			print termout

	def saveForecastedMotion(self,forecast,path,fname):
		T = forecast.shape[0]
		N = forecast.shape[1]
		D = forecast.shape[2]
		for j in range(N):
			motion = forecast[:,j,:]
			f = open('{0}{2}_N_{1}'.format(path,j,fname),'w')
			for i in range(T):
				st = ''
				for k in range(D):
					st += str(motion[i,k]) + ','
				st = st[:-1]
				f.write(st+'\n')
			f.close()
		
	'''Predicts future movements'''	
	def predict_sequence(self,teX,sequence_length=100):
		future_sequence = []
		for i in range(sequence_length):
			prediction = self.predict(teX,1e-5)
			prediction = prediction[-1]
			teX = np.append(teX,[prediction],axis=0)
			future_sequence.append(prediction)
		return np.array(future_sequence)

	def predict_output(self,teX,predictfn):
		prediction = self.predict(teX)
		shape = prediction.shape
		if prediction.ndim > 2:
			# prediction dim = T x N x D
			# Sequence prediction
			prediction = prediction.reshape(shape[0]*shape[1],shape[2])
			prediction = predictfn(prediction)
			prediction = prediction.reshape(shape[0],shape[1])
			# Output dim = T x N
		else:
			# prediction dim = N x D
			# Single prediction at the end of sequence
			prediction = predictfn(prediction)
			# Output dim = N
		return prediction
