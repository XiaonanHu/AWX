import numpy as np
import keras.backend as K

from copy import deepcopy
from keras.layers import Dense


class AWX(Dense):
    def __init__(
        self, A, n_norm=5, activation=None, use_bias=True, kernel_initializer='glorot_uniform', bias_initializer='zeros',
        kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None,
        **kwargs):
        
        self.n = n_norm
        self.leaves = A.sum(0) == 0
        self.A = np.zeros(A.shape)
        
        self.g = nx.DiGraph(A)
        self.g_d = nx.DiGraph(A.T)
        
        for i in np.where(self.leaves)[0]:
            ancestors = list(nx.descendants(self.g, i))
            if ancestors:
                self.A[i, ancestors] = 1
    
        self.A[self.leaves,self.leaves] = 1
        
        self.A = K.constant(self.A)
        self.leaves = K.constant(self.leaves)
        units = A.shape[0]
        
        super(AWX, self).__init__(
            units, activation=activation, use_bias=use_bias, kernel_initializer=kernel_initializer, 
            bias_initializer=bias_initializer, kernel_regularizer=kernel_regularizer, bias_regularizer=bias_regularizer,
            activity_regularizer=activity_regularizer,kernel_constraint=kernel_constraint, bias_constraint=bias_constraint, 
            **kwargs
        )
    
    def n_norm(self, x, epsilon=1e-20):
        return K.pow(K.clip(K.sum(K.pow(x, self.n), -1), epsilon, 1-epsilon), 1./self.n)

    def call(self, inputs):
        output = K.dot(inputs, self.kernel)
        if self.use_bias:
            output = K.bias_add(output, self.bias)
            
        if self.activation is not None:
            output = self.activation(output)
            
        if self.n > 1:
            output = self.n_norm(output.reshape((-1,)) * self.A.T).reshape((1,-1))
        elif self.n == 1:
            output = K.clip(K.dot(output, self.A), 0, 1)
        elif self.n == 0:
            output = K.max(output.reshape((-1,)) * self.A.T, -1).reshape((1,-1))
        
        return output