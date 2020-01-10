### import packages
import tskit
import tqdm
import numpy as np

### coalescent relationship matrix
def g(p):
  return 1/(p*(1-p))

def relevant_nodes(tree):
  N = tree.num_samples()
  rel_nodes = []
  for i in list(range(N)):
    c = i
    while not c in rel_nodes:
      if c == -1: 
        break
      rel_nodes.append(c)
      c = tree.parent(c)
  rel_nodes.sort()
  return rel_nodes

def zeta(tree, g):
  N = tree.num_samples()
  rel_nodes = relevant_nodes(tree)
  zetas = np.zeros([N, N])
  for c in rel_nodes:
    descendents = list(tree.samples(c))
    p = len(descendents) / N
    if(p == 0 or p == 1):
      continue
    q = (tree.time(tree.parent(c)) - tree.time(c)) * g(p)
    zetas[np.ix_(descendents, descendents)] += q
  return zetas

def epsilon(x):
  N = x.shape[0]
  mean = x.mean()
  colmean = np.tile(x.mean(axis = 0), (N, 1))
  rowmean = colmean.T
  return x + mean - colmean - rowmean

def getEK(tree):
  buffer = epsilon(zeta(tree, g))
  L = tree.total_branch_length
  return buffer/L

def getEK_trees(trees, flags = None, file = None):
  if (flags == None):
    flags = [True] * trees.num_trees
  elif len(flags) != trees.num_trees:
    print("incorrect flags length!")
  idx_trees = np.where(flags)[0].tolist()
  
  N = trees.num_samples
  EK = np.zeros([N, N])
  total_tl = 0
  pbar = tqdm.tqdm(total = len(idx_trees), 
                   bar_format = '{l_bar}{bar:30}{r_bar}{bar:-30b}',
                   miniters = len(idx_trees) // 100,
                   file = file)
  
  for i in idx_trees:
    tree = trees.at_index(i)
    interval = tree.interval
    tl = (interval[1] - interval[0]) * tree.total_branch_length * 1e-8
    total_tl += tl
    EK += getEK(tree) * tl
    pbar.update(1)
  EK /= total_tl
  pbar.close()
  return (EK, round(total_tl))

def get_flags(trees, variants, file = None):
    flags = [False] * trees.num_trees
    for v in tqdm.tqdm(variants, bar_format = '{l_bar}{bar:30}{r_bar}{bar:-30b}',
                       miniters = len(variants) // 100, 
                       file = file):
      flags[trees.at(v).index] = True
    return flags
