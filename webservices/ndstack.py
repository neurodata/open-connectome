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

import blosc
import numpy as np
from contextlib import closing
import MySQLdb
from PIL import Image
from ndcube.cube import Cube
import spatialdb
from spdb.s3io import S3IO
from ndingest.nddynamo.cuboidindexdb import CuboidIndexDB
from ndproj.ndproject import NDProject
from ndctypelib import XYZMorton, MortonXYZ, isotropicBuild_ctype, addDataToZSliceStack_ctype, addDataToIsotropicStack_ctype
from ndlib.ndtype import *
from ndwserror import NDWSError
from ndingest.settings.settings import Settings
ndsettings = Settings.load()
import logging
logger=logging.getLogger("neurodata")


"""Construct a hierarchy off of a completed database."""

def buildStack(token, channel_name, resolution=None):
  """Wrapper for the different datatypes """

  pr = NDProject.fromTokenName(token)
  ch = pr.getChannelObj(channel_name)

  try:
    if ch.channel_type in ANNOTATION_CHANNELS:
      if pr.kvengine == MYSQL:
        clearStack(pr, ch, resolution)
      buildAnnoStack(pr, ch, resolution)
    elif ch.channel_type in IMAGE_CHANNELS:
      buildImageStack(pr, ch, resolution)
    elif ch.channel_type in TIMESERIES_CHANNELS:
      buildImageStack(pr, ch, resolution)
    else:
      logger.error("Not Supported")
      raise NDWSError("Not Supported")
  
    ch.propagate = PROPAGATED
  
  except Exception as e:
    clearStack(pr, ch, resolution)
    ch.propagate = NOT_PROPAGATED
  except MySQLdb.Error as e:
    clearStack(pr, ch, resolution)
    ch.propagate = NOT_PROPAGATED
    # projdb.updatePropagate(proj)
    logger.error("Error in building image stack {}".format(token))
    raise NDWSError("Error in the building image stack {}".format(token))


def clearStack (proj, ch, res=None):
  """ Clear a ND stack for a given project """

  with closing(spatialdb.SpatialDB(proj)) as db:
    
    # pick a resolution
    if res is None:
      res = 1
    
    high_res = proj.datasetcfg.scalinglevels
    list_of_tables = []
    sql = ""
   
    # Creating a list of all tables to clear
    if ch.channel_datatype in ANNOTATION_CHANNELS:
      list_of_tables.append(ch.getRamonTable())
    for cur_res in range(res, high_res):
      list_of_tables.append(ch.getTable(cur_res))
      # list_of_tables.append(ch.getNearIsoTable(cur_res))
      if ch.channel_datatype in ANNOTATION_CHANNELS:
        list_of_tables.append(ch.getIdxTable(cur_res))
        list_of_tables.append(ch.getExceptionsTable(cur_res))

    # for anno_type in annotation.anno_dbtables.keys():
      # list_of_tables.append(ch.getAnnoTable(anno_type))

    # Creating the sql query to execute
    for table_name in list_of_tables:
      sql += "TRUNCATE table {};".format(table_name)
    
    # Executing the query to clear the tables
    try:
      db.kvio.conn.cursor().execute(sql)
      db.kvio.conn.commit()
    except MySQLdb.Error, e:
      logger.error ("Error truncating the table. {}".format(e))
      raise
    finally:
      db.kvio.conn.cursor().close()


def buildAnnoStack ( proj, ch, res=None ):
  """Build the hierarchy for annotations"""
  
  with closing(spatialdb.SpatialDB (proj)) as db:

    # pick a resolution
    if res is None:
      res = 1
    
    high_res = proj.datasetcfg.scalinglevels
    scaling = proj.datasetcfg.scalingoption
  
    for cur_res in range(res, high_res+1):

      # Get the source database sizes
      [ximagesz, yimagesz, zimagesz] = proj.datasetcfg.dataset_dim(cur_res-1)
      timerange = ch.time_range
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.get_cubedim(cur_res-1)

      # Set the limits for iteration on the number of cubes in each dimension
      xlimit = (ximagesz-1) / xcubedim + 1
      ylimit = (yimagesz-1) / ycubedim + 1
      zlimit = (zimagesz-1) / zcubedim + 1

      # choose constants that work for all resolutions. 
      # recall that cube size changes from 128x128x16 to 64*64*64 with res
      if scaling == ZSLICES:
        outdata = np.zeros([zcubedim*4, ycubedim*2, xcubedim*2], dtype=ND_dtypetonp.get(ch.channel_datatype))
      elif scaling == ISOTROPIC:
        outdata = np.zeros([zcubedim*2, ycubedim*2, xcubedim*2], dtype=ND_dtypetonp.get(ch.channel_datatype))
      else:
        logger.error("Invalid scaling option in project = {}".format(scaling) )
        raise NDWSError("Invalid scaling option in project = {}".format(scaling)) 

      # Round up to the top of the range
      lastzindex = (XYZMorton([xlimit,ylimit,zlimit])/64+1)*64

      # Iterate over the cubes in morton order
      for mortonidx in range(0, lastzindex, 64): 

        # call the range query
        cuboids = db.getCubes(ch, range(mortonidx,mortonidx+64), cur_res-1)
        cube = Cube.CubeFactory(cubedim, ch.channel_type, ch.channel_datatype)

        # get the first cube
        for idx, datastring in cuboids:

          xyz = MortonXYZ(idx)
          if db.NPZ:
            cube.fromNPZ(datastring)
          else:
            cube.fromBlosc(datastring)

          if scaling == ZSLICES:

            # Compute the offset in the output data cube 
            #  we are placing 4x4x4 input blocks into a 2x2x4 cube 
            offset = [(xyz[0]%4)*(xcubedim/2), (xyz[1]%4)*(ycubedim/2), (xyz[2]%4)*zcubedim]
            # add the contribution of the cube in the hierarchy
            addDataToZSliceStack_ctype(cube, outdata, offset)

          elif scaling == ISOTROPIC:

            # Compute the offset in the output data cube 
            #  we are placing 4x4x4 input blocks into a 2x2x2 cube 
            offset = [(xyz[0]%4)*(xcubedim/2), (xyz[1]%4)*(ycubedim/2), (xyz[2]%4)*(zcubedim/2)]

            # use python version for debugging
            addDataToIsotropicStack_ctype(cube, outdata, offset)

        #  Get the base location of this batch
        xyzout = MortonXYZ (mortonidx)

        # adjust to output corner for scale.
        if scaling == ZSLICES:
          outcorner = [xyzout[0]*xcubedim/2, xyzout[1]*ycubedim/2, xyzout[2]*zcubedim]
        elif scaling == ISOTROPIC:
          outcorner = [xyzout[0]*xcubedim/2, xyzout[1]*ycubedim/2, xyzout[2]*zcubedim/2]

        #  Data stored in z,y,x order dims in x,y,z
        outdim = outdata.shape[::-1]

        # Preserve annotations made at the specified level
        # KL check that the P option preserves annotations?  RB changed from O
        db.annotateDense(ch, outcorner, cur_res, outdata, 'O')
        db.kvio.conn.commit()
          
        # zero the output buffer
        outdata = np.zeros ([zcubedim*4, ycubedim*2, xcubedim*2], dtype=ND_dtypetonp.get(ch.channel_datatype))


def buildImageStack(proj, ch, res=None):
  """Build the hierarchy of images"""
  
  with closing(spatialdb.SpatialDB(proj)) as db:
    
    s3_io = S3IO(db)
    cuboidindex_db = CuboidIndexDB(proj.project_name, endpoint_url=ndsettings.DYNAMO_ENDPOINT)
    # pick a resolution
    if res is None:
      res = 1

    high_res = proj.datasetcfg.scalinglevels
    scaling = proj.datasetcfg.scalingoption

    for cur_res in range (res, high_res+1):

      # Get the source database sizes
      [ximagesz, yimagesz, zimagesz] = proj.datasetcfg.dataset_dim(cur_res)
      timerange = ch.time_range
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.get_cubedim(cur_res)
      [xsupercubedim, ysupercubedim, zsupercubedim] = supercubedim = proj.datasetcfg.get_supercubedim(cur_res)

      if scaling == ZSLICES:
        (xscale, yscale, zscale) = (2, 2, 1)
      elif scaling == ISOTROPIC:
        (xscale, yscale, zscale) = (2, 2, 2)
      else:
        logger.error("Invalid scaling option in project = {}".format(scaling))
        raise NDWSError("Invalid scaling option in project = {}".format(scaling)) 

      biggercubedim = [xsupercubedim*xscale, ysupercubedim*yscale, zsupercubedim*zscale]

      # Set the limits for iteration on the number of cubes in each dimension
      xlimit = (ximagesz-1) / xsupercubedim + 1
      ylimit = (yimagesz-1) / ysupercubedim + 1
      zlimit = (zimagesz-1) / zsupercubedim + 1

      # Iterating over time
      for ts in range(timerange[0], timerange[1]+1, 1):
        # Iterating over zslice
        for z in range(zlimit):
          # Iterating over y
          for y in range(ylimit):
            # Iterating over x
            for x in range(xlimit):

              # cutout the data at the resolution
              if ch.channel_type not in TIMESERIES_CHANNELS:
                olddata = db.cutout(ch, [x*xscale*xsupercubedim, y*yscale*ysupercubedim, z*zscale*zsupercubedim ], biggercubedim, cur_res-1).data
              else:
                olddata = db.timecutout(ch, [x*xscale*xsupercubedim, y*yscale*ysupercubedim, z*zscale*zsupercubedim ], biggercubedim, cur_res-1, [ts,ts+1]).data
                olddata = olddata[0,:,:,:]

              #olddata target array for the new data (z,y,x) order
              newdata = np.zeros([zsupercubedim, ysupercubedim, xsupercubedim], dtype=ND_dtypetonp.get(ch.channel_datatype))

              for sl in range(zsupercubedim):

                if scaling == ZSLICES:
                  data = olddata[sl,:,:]
                elif scaling == ISOTROPIC:
                  data = isotropicBuild_ctype(olddata[sl*2,:,:], olddata[sl*2+1,:,:])

                # Convert each slice to an image
                # 8-bit int option
                if olddata.dtype == np.uint8:
                  slimage = Image.frombuffer('L', (xsupercubedim*2, ysupercubedim*2), data.flatten(), 'raw', 'L', 0, 1)
                # 16-bit int option
                elif olddata.dtype == np.uint16:
                  slimage = Image.frombuffer('I;16', (xsupercubedim*2,ysupercubedim*2), data.flatten(), 'raw', 'I;16', 0, 1)
                # 32-bit float option
                elif olddata.dtype == np.float32:
                  slimage = Image.frombuffer('F', (xsupercubedim * 2, ysupercubedim * 2), data.flatten(), 'raw', 'F', 0, 1)
                # 32 bit RGBA data
                elif olddata.dtype == np.uint32:
                  slimage = Image.fromarray( data, "RGBA" )
                # KL TODO Add support for 32bit and 64bit RGBA data

                # Resize the image and put in the new cube array
                if olddata.dtype != np.uint32:
                  newdata[sl, :, :] = np.asarray(slimage.resize([xsupercubedim, ysupercubedim]))
                else:
                  tempdata = np.asarray(slimage.resize([xsupercubedim, ysupercubedim]))
                  newdata[sl,:,:] = np.left_shift(tempdata[:,:,3], 24, dtype=np.uint32) | np.left_shift(tempdata[:,:,2], 16, dtype=np.uint32) | np.left_shift(tempdata[:,:,1], 8, dtype=np.uint32) | np.uint32(tempdata[:,:,0])

              zidx = XYZMorton ([x,y,z])
              cube = Cube.CubeFactory(supercubedim, ch.channel_type, ch.channel_datatype)
              cube.zeros()

              cube.data = newdata
              # KL TODO test this
<<<<<<< HEAD
              # KLTODO putCube/getCube to have neariso argument
              # RBTODO do neariso for mysql end to end and then integrate with 
              if ch.channel_type in TIMESERIES_CHANNELS:
                db.putCube(ch, zidx, cur_res, cube, timestamp=ts, update=True)
              else:
                db.putCube(ch, zidx, cur_res, cube, timestamp=None, update=True)
=======
              s3_io.putCube(ch, cur_res, zidx, blosc.pack_array(cube.data))
              # if ch.channel_type in TIMESERIES_CHANNELS:
                # db.putCube(ch, zidx, cur_res, cube, timestamp=ts, update=True)
              # else:
                # db.putCube(ch, zidx, cur_res, cube, timestamp=None, update=True)
>>>>>>> microns
