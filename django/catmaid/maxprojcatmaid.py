# Copyright 2014 NeuroData (http://neurodata.io)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import django
import re
import numpy as np
import cStringIO
import math
from contextlib import closing

import restargs
import spatialdb
import ndproj
import ndwsrest
import mcfc

from ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

class MaxProjCatmaid:
  """Prefetch CATMAID tiles into MndcheDB"""

  def __init__(self):

    self.proj = None
    self.db = None
    self.token = None
    self.tilesz = 512
    self.colors = ('C','M','Y','R','G','B')
    self.channel_list = None

  def __del__(self):
    pass

  def getTileXY ( self, res, xtile, ytile, zslice, width ):
    """Cutout, return the image"""

    # figure out the cutout (limit to max image size)
    xstart = xtile*self.tilesz
    ystart = ytile*self.tilesz
    xend = min ((xtile+1)*self.tilesz,self.proj.datasetcfg.imageSize(res)[0][0])
    yend = min ((ytile+1)*self.tilesz,self.proj.datasetcfg.imageSize(res)[0][1])

    zstart = max(zslice-width,0)
    zend = min(zslice+1+width,self.tilesz,self.proj.datasetcfg.imageSize(res)[0][2]) 

    # call the mcfc interface
    imageargs = '{}/{},{}/{},{}/{},{}/'.format(res, xstart, xend, ystart, yend, zstart, zend) 

    tiledata = None
    for index, channel_name in enumerate(self.channel_list):
      ch = self.proj.getChannelObj(channel_name)
      cutout = ndwsrest.cutout(imageargs, ch, self.proj, self.db)
      # initialize the tiledata by type
      if tiledata == None:
        tiledata = np.zeros((len(self.channel_list), self.tilesz, self.tilesz), dtype=cutout.data.dtype)

      tiledata[index, 0:((yend-1)%self.tilesz+1), 0:((xend-1)%self.tilesz+1)] = np.amax(cutout.data, axis=0)
      tiledata[index,:] = ndwsrest.window(tiledata[index,:], ch)
    
    # We have an compound array.  Now color it.
    return mcfc.mcfcPNG (tiledata, self.colors)


  def getTile ( self, webargs ):
    """Either fetch the file from mndche or get a mcfc image"""

    try:
      # arguments of format /token/channel/(?:width:3)/slice_type/z/x_y_res.png
      m = re.match("(\w+)/([\w+,[:\w]*]*)(?:/width:([\d+]+))?/(xy|yz|xz)/(\d+)/(\d+)_(\d+)_(\d+).png", webargs)

      [self.token, channels, widthstr, slice_type] = [i for i in m.groups()[:4]]
      [ztile, ytile, xtile, res] = [int(i) for i in m.groups()[4:]]

      # extract the width as an integer
      width = int(widthstr)

      # check for channel_name:color and put them in the designated list
      try:
        self.channel_list, colors = zip(*re.findall("(\w+)[:]?(\w)?", channels))
        # checking for a non-empty list
        if filter(None, colors):
          # if it is a mixed then replace the missing ones with the existing schema
          self.colors = [ b if a is u'' else a for a,b in zip(colors, self.colors)]
      except Exception, e:
        logger.warning("Incorrect channel formst for getTile {}. {}".format(channels, e))
        raise NDWSError("Incorrect channel format for getTile {}. {}".format(channels, e))
      
    except Exception, e:
      logger.warning("Incorrect arguments for getTile {}. {}".format(webargs, e))
      raise NDWSError("Incorrect arguments for getTile {}. {}".format(webargs, e))

    with closing ( ndproj.NDProjectsDB() ) as projdb:
      self.proj = projdb.loadToken ( self.token )

    with closing ( spatialdb.SpatialDB(self.proj) ) as self.db:
      
      tile = None
      
      if tile == None:

        if slice_type == 'xy':
          img = self.getTileXY(res, xtile, ytile, ztile, width)
#        elif slice_type == 'xz':
#          img = self.getTileXZ(res, xtile, ytile, ztile, width)
#        elif slice_type == 'yz':
#          img = self.getTileYZ(res, xtile, ytile, ztile, width)
        else:
          logger.warning ("Requested illegal image plane {}. Should be xy, xz, yz.".format(slice_type))
          raise NDWSError ("Requested illegal image plane {}. Should be xy, xz, yz.".format(slice_type))
        
        fobj = cStringIO.StringIO ( )
        img.save ( fobj, "PNG" )

      else:
        fobj = cStringIO.StringIO(tile)

      fobj.seek(0)
      return fobj