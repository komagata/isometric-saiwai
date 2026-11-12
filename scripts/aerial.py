"""Projected GSI seamlessphoto mosaic at GROUND_RES; row zero is north."""
import numpy as np
from config import BUILD,GROUND_RES,XMIN,YMAX

def load_aerial():return np.load(BUILD/'aerial.npy',mmap_mode='r')
def world_to_px(xy):
    xy=np.asarray(xy,dtype=float)
    return np.stack([(xy[:,0]-XMIN)/GROUND_RES,(YMAX-xy[:,1])/GROUND_RES],axis=-1)
