# -*- coding: utf-8 -*-
"""
Created on Sun Oct  5 17:21:00 2014

@author: akusok
"""

import numpy as np
from mpi4py import MPI
from time import time
import resource
from memory_profiler import memory_usage

        
#@profile
def run():
    
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    n = 10002
    d = 42
    nn = 249
    
    # distribute projection matrix
    if rank == 0:
        W = np.random.rand(d,nn)
    else:
        W = None
    W = comm.bcast(W, root=0)
    print "%d W: "%rank, W.shape
    
    
    # distribute nonlinear transformation function
    if rank == 0:
        F = []
        #F.extend([np.array]*(nn-1))  # 7.25
        #F.extend([np.asarray]*(nn-1))  # 9.42
        F.extend([np.copy]*(nn-1))  # 7.58
        F.extend([np.tanh])
    else:
        F = None
    F = comm.bcast(F, root=0)
        
    t = time()
    if rank == 0:
        # get correct batch size
        X = np.random.randn(n,d)
        batch = n / size
        if size*batch < n:
            batch += 1
    else:
        batch = None
        n = None
        d = None
    batch = comm.bcast(batch, root=0)
    n = comm.bcast(n, root=0)
    d = comm.bcast(d, root=0)
    

    if rank == 0:
        # split and distribute data X
        for rec in range(1,size):
            comm.Isend([X[batch*rec: batch*(rec+1)], MPI.DOUBLE], dest=rec, tag=1)            
        X1 = X[:batch]
    else:
        X1 = np.empty((batch, d), dtype=np.float64)
        comm.Recv([X1, MPI.DOUBLE], source=0, tag=1)
    
    
    # do computations
    H1 = X1.dot(W)
    t2 = time()
    for i in range(len(F)):
        H1[:,i] = F[i](H1[:,i])
    H1 = H1.T.dot(H1) 
    print "func", time()-t2
    H = np.empty(H1.shape) 
    comm.Allreduce([H1, MPI.DOUBLE], [H, MPI.DOUBLE], op=MPI.SUM) 

    if rank == 0:
        print H.shape
    del H1
    
    if rank == 0:
        print time()-t


    #'''
    # check correctness
    if rank == 0:
        H2 = X.dot(W)
        H2[:,-1] = np.tanh(H2[:,-1]) 
        H2 = H2.T.dot(H2)
        
        print rank, "matrix H is correct: ", np.allclose(H2, H)    
        assert(np.allclose(H2, H))
    #'''    
    
    print "%d done!" % rank, "mem %.0fMB"%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**10)


if __name__ == "__main__":
    run()
    #mem_usage = memory_usage(run)
    #print('Memory usage (in chunks of .1 seconds): %s' % mem_usage)
    #print('Maximum memory usage: %s' % max(mem_usage))








