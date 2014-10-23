# Copyright 2014 Open Connectome Project (http://openconnecto.me)
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

import sys
import StringIO
import tempfile
import numpy as np
import zlib
import h5py
import os
import cStringIO
import csv
import re
import json
from PIL import Image
import MySQLdb
import itertools
from contextlib import closing

import restargs
import anncube
import ocpcadb
import ocpcaproj
import ocpcachannel
import h5ann
import h5projinfo
import annotation

from ocpca_cy import assignVoxels_cy
from ocpca_cy import recolor_cy

from ocpcaerror import OCPCAError

from windowcutout import windowCutout
import ocplib
import ocpcaprivate

import logging
logger=logging.getLogger("ocp")


#
#  ocpcarest: RESTful interface to annotations and cutouts
#

def cutout ( imageargs, proj, db, channel=None ):
  """Build the returned cube of data.  This method is called by all
       of the more basic services to build the data.
       They then format and refine the output."""

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.cutoutArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  filterlist = args.getFilter()
  zscaling = args.getZScaling()

  # Perform the cutout
  cube = db.cutout ( corner, dim, resolution, channel, zscaling )
  if filterlist != None:
    cube.data = ocplib.filter_ctype_OMP ( cube.data, filterlist )

  return cube

#
#  Return a Flat binary file zipped (for Stefan) 
#
def binZip ( imageargs, proj, db ):
  """Return a web readable Numpy Pickle zipped"""

  # if it's a channel database, pull out the channel
  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
    [ channel, sym, imageargs ] = imageargs.partition ('/')
  else: 
    channel = None

  cube = cutout ( imageargs, proj, db, channel )

  # Create the compressed cube
  cdz = zlib.compress ( cube.data.tostring()) 

  # Package the object as a Web readable file handle
  fileobj = cStringIO.StringIO ( cdz )
  fileobj.seek(0)
  return fileobj.read()

#
#  Return a Numpy Pickle zipped
#
def numpyZip ( imageargs, proj, db ):
  """Return a web readable Numpy Pickle zipped"""

  # if it's a channel database, pull out the channels and return a 4-d numpy array
  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:

    [ chanurl, sym, imageargs ] = imageargs.partition ('/')

    # make sure that the channels are ints
    channels = chanurl.split(',')

    chanobj = ocpcachannel.OCPCAChannels ( db )
    chanids = chanobj.rewriteToInts ( channels )

    ccdata = cutout ( imageargs, proj, db, chanids[0] ).data
    cubedata = np.zeros ( (len(chanids),ccdata.shape[0],ccdata.shape[1],ccdata.shape[2]) , dtype=ccdata.dtype )
    cubedata[0,:,:,:] = ccdata
    for i in range(1,len(chanids)):
      # allow 0 channels to be a noop for mcfc catmaid requests to choose color
      if chanids[i] == 0:
        continue
      else:
        cubedata[i,:,:,:] = cutout ( imageargs, proj, db, chanids[i] ).data

  # single channel cutout
  else: 
    channel = None
    cubedata = cutout ( imageargs, proj, db, channel ).data

  # Create the compressed cube
  fileobj = cStringIO.StringIO ()
  np.save ( fileobj, cubedata )
  cdz = zlib.compress (fileobj.getvalue()) 

  # Package the object as a Web readable file handle
  fileobj = cStringIO.StringIO ( cdz )
  fileobj.seek(0)
  return fileobj.read()

#
#  Return a HDF5 file
#
def HDF5 ( imageargs, proj, db ):
  """Return a web readable HDF5 file"""

  # Create an in-memory HDF5 file
  tmpfile = tempfile.NamedTemporaryFile ()
  fh5out = h5py.File ( tmpfile.name )

  try: 

    # if it's a channel database, pull out the channels
    if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
     
      [ chanurl, sym, imageargs ] = imageargs.partition ('/')

      # make sure that the channels are ints
      channels = chanurl.split(',')

      chanobj = ocpcachannel.OCPCAChannels ( db )
      chanids = chanobj.rewriteToInts ( channels )

      for i in range(len(chanids)):
        cube = cutout ( imageargs, proj, db, chanids[i] )
        changrp = fh5out.create_group( "CUTOUT" )
        changrp.create_dataset ( "{}".format(channels[i]), tuple(cube.data.shape), cube.data.dtype, compression='gzip', data=cube.data )
    
    elif proj.getDBType() == ocpcaproj.RGB_32bit or proj.getDBType() == ocpcaproj.RGB_64bit:
      cube = cutout ( imageargs, proj, db, None)
      cube.RGBAChannel()
      fh5out.create_dataset ( "CUTOUT", tuple(cube.data.shape), cube.data.dtype,\
                                  compression='gzip', data=cube.data )
    else: 
      cube = cutout ( imageargs, proj, db, None )
      fh5out.create_dataset ( "CUTOUT", tuple(cube.data.shape), cube.data.dtype,\
                                  compression='gzip', data=cube.data )

    fh5out.create_dataset( "DATATYPE", (1,), dtype=np.uint32, data=proj._dbtype )
  

  except:
    tmpfile.close()
    fh5out.close()
    raise

  fh5out.close()
  tmpfile.seek(0)
  return tmpfile.read()
  


#
#  **Image return a readable png object
#    where ** is xy, xz, yz
#
def xySlice ( imageargs, proj, db ):
  """Return the cube object for an xy plane"""
  
  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
    [ channel, sym, imageargs ] = imageargs.partition ('/')
    # make sure that the channel is an int identifier
    channel = ocpcachannel.toID ( channel, db ) 
  else: 
    channel = None

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ()
    args.xyArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  filterlist = args.getFilter()
  window = args.getWindow()
  (startwindow,endwindow) = proj.datasetcfg.windowrange
  
  # Perform the cutout
  cube = db.cutout ( corner, dim, resolution, channel )
  
  # Window Function - used to limit the range of data purely for viewing purposes
  if window != None or ( endwindow !=0 ):
    # Check which case is calling the window Function and assign the correct value
    if window == None:
      window = (startwindow, endwindow)

    windowCutout ( cube.data, window)
  
  # Filter Function - Eliminate unwanted synapses ids
  if filterlist != None:
    
    #filterCutout ( cube.data, filterlist )
    cube.data = ocplib.filter_ctype_OMP( cube.data, filterlist )
	  
    # calling the ctype filter function
  	# cube.data = filterCutoutCtype ( cube.data, filterlist )
	  #cube.data = filterCutoutCtypeOMP ( cube.data, filterlist )
    # inline vectorized is actually slower
    # vec_func = np.vectorize ( lambda x: 0 if x not in filterlist else x )
    # cube.data = vec_func ( cube.data )

  return cube


def xyImage ( imageargs, proj, db ):
  """Return an xy plane fileobj.read()"""
  cb = xySlice ( imageargs, proj, db )
#  if proj.getDBType() == ocpcaproj.CHANNELS:
#    fileobj = tempfile.NamedTemporaryFile()
#    cb.xySlice ( fileobj.name )
#  else:
  fileobj = cStringIO.StringIO ( )
  cb.xySlice ( fileobj )
  fileobj.seek(0)
  return fileobj.read()

def xzSlice ( imageargs, proj, db ):
  """Return an xz plane cube"""

  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
    [ channel, sym, imageargs ] = imageargs.partition ('/')
    # make sure that the channel is an int identifier
    channel = ocpcachannel.toID ( channel, db ) 
  else: 
    channel = None

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.xzArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  filterlist = args.getFilter()
  window = args.getWindow()
  (startwindow,endwindow) = proj.datasetcfg.windowrange

  # Perform the cutout
  cube = db.cutout ( corner, dim, resolution, channel )

  # Window Function - used to limit the range of data purely for viewing purposes
  if window != None or ( endwindow !=0 ):
    # Check which case is calling the window Function and assign the correct value
    if window == None:
      window = (startwindow, endwindow)

    windowCutout ( cube.data, window)
  
  # Filter Function - Eliminate unwanted synapses ids
  if filterlist != None:
    
    #filterCutout ( cube.data, filterlist )
    cube.data = ocplib.filter_ctype_OMP( cube.data, filterlist )
  
  return cube


def xzImage ( imageargs, proj, db ):
  """Return an xz plane fileobj.read()"""

  # little awkward because we need resolution here
  # it will be reparse in xzSlice
  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
    channel, sym, rest = imageargs.partition("/")
    resolution, sym, rest = rest.partition("/")
  else:
    resolution, sym, rest = imageargs.partition("/")

  cb = xzSlice ( imageargs, proj, db )
  fileobj = cStringIO.StringIO ( )
  cb.xzSlice ( proj.datasetcfg.zscale[int(resolution)], fileobj )

  fileobj.seek(0)
  return fileobj.read()


def yzSlice ( imageargs, proj, db ):
  """Return an yz plane as a cube"""

  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
    [ channel, sym, imageargs ] = imageargs.partition ('/')
  else: 
    channel = None

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.yzArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  filterlist = args.getFilter()
  window = args.getWindow()
  (startwindow,endwindow) = proj.datasetcfg.windowrange

  # Perform the cutout
  cube = db.cutout ( corner, dim, resolution, channel )
  
  # Window Function - used to limit the range of data purely for viewing purposes
  if window != None or ( endwindow !=0 ):
    # Check which case is calling the window Function and assign the correct value
    if window == None:
      window = (startwindow, endwindow)

    windowCutout ( cube.data, window)
  
  # Filter Function - Eliminate unwanted synapses ids
  if filterlist != None:
    
    #filterCutout ( cube.data, filterlist )
    cube.data = ocplib.filter_ctype_OMP( cube.data, filterlist )

  return cube


def yzImage ( imageargs, proj, db ):
  """Return an yz plane fileobj.read()"""

  # little awkward because we need resolution here
  # it will be reparse in xzSlice
  if proj.getDBType() == ocpcaproj.CHANNELS_8bit or proj.getDBType() == ocpcaproj.CHANNELS_16bit:
    channel, sym, rest = imageargs.partition("/")
    resolution, sym, rest = rest.partition("/")
  else:
    resolution, sym, rest = imageargs.partition("/")

  cb = yzSlice ( imageargs, proj, db )
  fileobj = cStringIO.StringIO ( )
  cb.yzSlice ( proj.datasetcfg.zscale[int(resolution)], fileobj )

  fileobj.seek(0)
  return fileobj.read()


#
#  Read individual annotations xyAnno, xzAnno, yzAnno
#
def xyAnno ( imageargs, proj, db ):
  """Return an xy plane fileobj.read() for a single objects"""

  [ annoidstr, sym, imageargs ] = imageargs.partition('/')
  annoids = [int(x) for x in annoidstr.split(',')]

  # retrieve the annotation 
  if len(annoids) == 1:
    anno = db.getAnnotation ( annoids[0] )
    if anno == None:
      logger.warning("No annotation found at identifier = %s" % (annoid))
      raise OCPCAError ("No annotation found at identifier = %s" % (annoid))
    else:
      iscompound = True if anno.__class__ in [ annotation.AnnNeuron ] else False; 
  else:
    iscompound = False

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.xyArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e.value)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()

  # determine if it is a compound type (NEURON) and get the list of relevant segments
  if iscompound:
    # remap the ids for a neuron
    dataids = db.getChildren ( annoids[0] ) 
    cb = db.annoCutout ( dataids, resolution, corner, dim, annoids[0] )
  else:
    # no remap when not a neuron
    dataids = annoids
    cb = db.annoCutout ( dataids, resolution, corner, dim, None )


  fileobj = cStringIO.StringIO ( )
  cb.xySlice ( fileobj )

  fileobj.seek(0)
  return fileobj.read()


def xzAnno ( imageargs, proj, db ):
  """Return an xz plane fileobj.read()"""

  [ annoidstr, sym, imageargs ] = imageargs.partition('/')
  annoids = [int(x) for x in annoidstr.split(',')]

  # retrieve the annotation 
  if len(annoids) == 1:
    anno = db.getAnnotation ( annoids[0] )
    if anno == None:
      logger.warning("No annotation found at identifier = %s" % (annoid))
      raise OCPCAError ("No annotation found at identifier = %s" % (annoid))
    else:
      iscompound = True if anno.__class__ in [ annotation.AnnNeuron ] else False; 
  else:
    iscompound = False

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.xzArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()

  # determine if it is a compound type (NEURON) and get the list of relevant segments
  if iscompound:
    # remap the ids for a neuron
    dataids = db.getChildren ( annoids[0] ) 
    cb = db.annoCutout ( dataids, resolution, corner, dim, annoids[0] )
  else:
    # no remap when not a neuron
    cb = db.annoCutout ( annoids, resolution, corner, dim, None )

  fileobj = cStringIO.StringIO ( )
  cb.xzSlice ( proj.datasetcfg.zscale[resolution], fileobj )

  fileobj.seek(0)
  return fileobj.read()


def yzAnno ( imageargs, proj, db ):
  """Return an yz plane fileobj.read()"""

  [ annoidstr, sym, imageargs ] = imageargs.partition('/')
  annoids = [int(x) for x in annoidstr.split(',')]

  # retrieve the annotation 
  if len(annoids) == 1:
    anno = db.getAnnotation ( annoids[0] )
    if anno == None:
      logger.warning("No annotation found at identifier = %s" % (annoid))
      raise OCPCAError ("No annotation found at identifier = %s" % (annoid))
    else:
      iscompound = True if anno.__class__ in [ annotation.AnnNeuron ] else False; 
  else:
    iscompound = False

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.yzArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()

  # determine if it is a compound type (NEURON) and get the list of relevant segments
  if iscompound:
    # remap the ids for a neuron
    dataids = db.getChildren ( annoids[0] ) 
    cb = db.annoCutout ( dataids, resolution, corner, dim, annoids[0] )
  else:
    # no remap when not a neuron
    cb = db.annoCutout ( annoids, resolution, corner, dim, None )

  fileobj = cStringIO.StringIO ( )
  cb.yzSlice ( proj.datasetcfg.zscale[resolution], fileobj )

  fileobj.seek(0)
  return fileobj.read()

#
#  annId
#    return the annotation identifier of a pixel
#
def annId ( imageargs, proj, db ):
  """Return the annotation identifier of a voxel"""

  # Perform argument processing
  (resolution, voxel) = restargs.voxel ( imageargs, proj.datasetcfg )

  # Get the identifier
  return db.getVoxel ( resolution, voxel )


#
#  listIds
#  return the annotation identifiers in a region                         
#                                                                         
def listIds ( imageargs, proj,db ):
  """Return the list of annotation identifiers in a region"""

  # Perform argument processing
  try:
    args = restargs.BrainRestArgs ();
    args.cutoutArgs ( imageargs, proj.datasetcfg )
  except restargs.RESTArgsError, e:
    logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
    raise OCPCAError(e)

  # Extract the relevant values
  corner = args.getCorner()
  dim = args.getDim()
  resolution = args.getResolution()
  
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    cb = db.cutout ( corner, dim, resolution )
    ids =  np.unique(cb.data)

  idstr=''.join([`id`+', ' for id in ids])
  
  idstr1 = idstr.lstrip('0,')
  return idstr1.rstrip(', ')

#
#  Select the service that you want.
#  Truncate this from the arguments and past 
#  the rest of the RESTful arguments to the 
#  appropriate function.  At this point, we have a 
#  data set and a service.
#
def selectService ( webargs, proj, db ):
  """Parse the first arg and call service, HDF5, npz, etc."""

  [ service, sym, rangeargs ] = webargs.partition ('/')
  
  if service == 'xy':
    return xyImage ( rangeargs, proj, db )

  elif service == 'xz':
    return xzImage ( rangeargs, proj, db)

  elif service == 'yz':
    return yzImage ( rangeargs, proj, db )

  elif service == 'hdf5':
    return HDF5 ( rangeargs, proj, db )

  elif service == 'npz':
    return  numpyZip ( rangeargs, proj, db ) 

  elif service == 'zip':
    return  binZip ( rangeargs, proj, db ) 

  elif service == 'id':
    return annId ( rangeargs, proj, db )
  
  elif service == 'ids':
    return listIds ( rangeargs, proj, db )

  elif service == 'xyanno':
    return xyAnno ( rangeargs, proj, db )

  elif service == 'xzanno':
    return xzAnno ( rangeargs, proj, db )

  elif service == 'yzanno':
    return yzAnno ( rangeargs, proj, db )

  else:
    logger.warning("An illegal Web GET service was requested %s.  Args %s" % ( service, webargs ))
    raise OCPCAError ("No such Web service: %s" % service )


#
#  Select the service that you want.
#  Truncate this from the arguments and past 
#  the rest of the RESTful arguments to the 
#  appropriate function.  At this point, we have a 
#  data set and a service.
#
def selectPost ( webargs, proj, db, postdata ):
  """Parse the first arg and call the right post service"""

  [ service, sym, postargs ] = webargs.partition ('/')
  # Don't write to readonly projects
  if proj.getReadOnly()==1:
    logger.warning("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
    raise OCPCAError("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))

  # choose to overwrite (default), preserve, or make exception lists
  #  when voxels conflict
  # Perform argument processing

  # Bind the annotation database
  db.startTxn()

  tries = 0
  done = False

  while not done and tries < 5:

    try:

      if service == 'npz':

        # Process the arguments
        try:
          args = restargs.BrainRestArgs ();
          args.cutoutArgs ( postargs, proj.datasetcfg )
        except restargs.RESTArgsError, e:
          logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
          raise OCPCAError(e)

        corner = args.getCorner()
        resolution = args.getResolution()

        # This is used for ingest only now.  So, overwrite conflict option.
        conflictopt = restargs.conflictOption ( "" )

        # get the data out of the compressed blob
        rawdata = zlib.decompress ( postdata )
        fileobj = cStringIO.StringIO ( rawdata )
        voxarray = np.load ( fileobj )

        if proj.getDBType() != ocpcaproj.ANNOTATIONS and proj.getDBType() != ocpcaproj.ANNOTATIONS_64bit: 

          db.writeCuboid ( corner, resolution, voxarray )
          # this is just a status
          entityid=0

        # Choose the verb, get the entity (as needed), and annotate
        # Translates the values directly
        else:

          entityid = db.annotateDense ( corner, resolution, voxarray, conflictopt )

      elif service == 'hdf5':
    
        # Process the arguments
        try:
          args = restargs.BrainRestArgs ();
          args.cutoutArgs ( postargs, proj.datasetcfg )
        except restargs.RESTArgsError, e:
          logger.warning("REST Arguments %s failed: %s" % (postargs,e))
          raise OCPCAError(e)

        corner = args.getCorner()
        resolution = args.getResolution()

        # This is used for ingest only now.  So, overwrite conflict option.
        conflictopt = restargs.conflictOption ( "" )

        # Get the HDF5 file.
        tmpfile = tempfile.NamedTemporaryFile ( )
# RB? where did this come from
#        self.idgrp.create_dataset ( "VOXELS", (len(voxlist),3), np.uint32, data=voxlist )     
        tmpfile.write ( postdata )
        tmpfile.seek(0)
        h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

        voxarray = np.array(h5f.get('CUTOUT'))

        if proj.getDBType() != ocpcaproj.ANNOTATIONS and proj.getDBType() != ocpcaproj.ANNOTATIONS_64bit: 

          db.writeCuboid ( corner, resolution, voxarray )
          # this is just a status
          entityid=0

        # Choose the verb, get the entity (as needed), and annotate
        # Translates the values directly
        else:

          entityid = db.annotateDense ( corner, resolution, voxarray, conflictopt )
      
      else:
        logger.warning("An illegal Web POST service was requested: %s.  Args %s" % ( service, webargs ))
        raise OCPCAError ("No such Web service: %s" % service )
        
      db.commit()
      done=True

    # rollback if you catch an error
    except MySQLdb.OperationalError, e:
      logger.warning ("Transaction did not complete. %s" % (e))
      tries += 1
      db.rollback()
      continue
    except MySQLdb.Error, e:
      logger.warning ("POST transaction rollback. %s" % (e))
      db.rollback()
      raise
    except Exception, e:
      logger.exception ("POST transaction rollback. %s" % (e))
      db.rollback()
      raise

  return str(entityid)

#
#  Interface to annotation by project.
#   Lookup the project token in the database and figure out the 
#   right database to load.
#
def getCutout ( webargs ):
  """Interface to the cutout service for annotations.
      Load the annotation project and invoke the appropriate
      dataset."""

  [ token, sym, rangeargs ] = webargs.partition ('/')

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    return selectService ( rangeargs, proj, db )


def putCutout ( webargs, postdata ):
  """Interface to the write cutout data.
      Load the annotation project and invoke the appropriate
      dataset."""

  [ token, sym, rangeargs ] = webargs.partition ('/')
  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    return selectPost ( rangeargs, proj, db, postdata )


def catmaid ( cmtilesz, token, plane, resolution, xtile, ytile, zslice, channel ):
  """Interface to the cutout service for catmaid request.  It does address translation."""

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
  
    # datatype from the project
    if proj.getDBType() == ocpcaproj.IMAGES_8bit or proj.getDBType == ocpcaproj.CHANNELS_8bit:
      datatype = np.uint8
    elif proj.getDBType() == ocpcaproj.CHANNELS_16bit or proj.getDBType() == ocpcaproj.IMAGES_16bit:
      datatype = np.uint16
    elif proj.getDBType() == ocpcaproj.RGB_32bit or proj.getDBType() == ocpcaproj.ANNOTATIONS or proj.     getDBType() == ocpcaproj.PROBMAP_32bit:
      datatype = np.uint32
    else:
      datatype = np.uint64

    # build the cutout request
    if plane=='xy':
     
      # figure out the cutout (limit to max image size)
      xstart = xtile*cmtilesz
      ystart = ytile*cmtilesz
      xend = min ((xtile+1)*cmtilesz,proj.datasetcfg.imagesz[resolution][0])
      yend = min ((ytile+1)*cmtilesz,proj.datasetcfg.imagesz[resolution][1])
      
      # Return empty data if request is outside bounds.  don't like it.
      if xstart>=xend or ystart>=yend:
        cutoutdata = np.zeros ( [cmtilesz,cmtilesz], dtype=datatype )

      else: 
        if proj.getDBType() == ocpcaproj.CHANNELS_16bit or proj.getDBType == ocpcaproj.CHANNELS_8bit:
          imageargs = '%s/%s/%s,%s/%s,%s/%s/' % ( channel, resolution, xstart, xend, ystart, yend, zslice )
        else:
          imageargs = '%s/%s,%s/%s,%s/%s/' % ( resolution, xstart, xend, ystart, yend, zslice )

        cb = xySlice ( imageargs, proj, db )

        # reshape (if it's not a full cutout)
        if cb.data.shape != [1,cmtilesz,cmtilesz]:
          cutoutdata = np.zeros ( [cmtilesz,cmtilesz], dtype=cb.data.dtype )
          cutoutdata[0:cb.data.shape[1],0:cb.data.shape[2]] = cb.data.reshape([cb.data.shape[1],cb.data.shape[2]])
        else:
          cutoutdata = cb.data.reshape([cmtilesz,cmtilesz])

    else:
      logger.warning("No such cutout plane: %s.  Must be (xy|xz|yz)..  Args %s" % ( service, webargs ))
      raise ANNError ( "No such cutout plane: %s.  Must be (xy|xz|yz)." % plane )
  
    cb.data = cutoutdata
    # Write the image to a readable stream
    cb.catmaidSlice()

    return cb.data


def ocpcacatmaid_legacy ( webargs ):
  """Interface to the cutout service for catmaid request.  It does address translation."""

  CM_TILESIZE=256
  token, plane, resstr, xtilestr, ytilestr, zslicestr, rest = webargs.split('/',7)

  # invoke general catmaid with a 0 channel argument
  return catmaid ( CM_TILESIZE, token, plane, int(resstr), int(xtilestr), int(ytilestr), int(zslicestr), 0 )


################# RAMON interfaces #######################


"""An enumeration for options processing in getAnnotation"""
AR_NODATA = 0
AR_VOXELS = 1
AR_CUTOUT = 2
AR_TIGHTCUTOUT = 3
AR_BOUNDINGBOX = 4
AR_CUBOIDS = 5


def getAnnoById ( annoid, h5f, proj, db, dataoption, resolution=None, corner=None, dim=None ): 
  """Retrieve the annotation and put it in the HDF5 file."""

  # aetrieve the annotation 
  anno = db.getAnnotation ( annoid )
  if anno == None:
    logger.warning("No annotation found at identifier = %s" % (annoid))
    raise OCPCAError ("No annotation found at identifier = %s" % (annoid))

  # create the HDF5 object
  h5anno = h5ann.AnnotationtoH5 ( anno, h5f )

  # only return data for annotation types that have data
  if anno.__class__ in [ annotation.AnnSeed ] and dataoption != AR_NODATA: 
    logger.warning("No data associated with annotation type %s" % ( anno.__class__))
    raise OCPCAError ("No data associated with annotation type %s" % ( anno.__class__))

  # determine if it is a compound type (NEURON) and get the list of relevant segments
  if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
    dataids = db.getChildren ( annoid ) 
  else:
    dataids = [anno.annid]

  # get the voxel data if requested
  if dataoption==AR_VOXELS:

  # RBTODO Need to make voxels zoom

    allvoxels = []

    # add voxels for all of the ids
    for dataid in dataids:
  
      voxlist = db.getLocations ( dataid, resolution ) 
      if len(voxlist) != 0:
        allvoxels =  allvoxels + voxlist 

    allvoxels = [ el for el in set ( [ tuple(t) for t in allvoxels ] ) ]
    h5anno.addVoxels ( resolution,  allvoxels )

  # support list of IDs to filter cutout
  elif dataoption==AR_CUTOUT:

    # cutout the data with the and remap for neurons.
    if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
      cb = db.annoCutout(dataids,resolution,corner,dim,annoid)
    else:
      # don't need to remap single annotations
      cb = db.annoCutout(dataids,resolution,corner,dim,None)

    # again an abstraction problem with corner.
    #  return the corner to cutout arguments space
    retcorner = [corner[0], corner[1], corner[2]+proj.datasetcfg.slicerange[0]]
    h5anno.addCutout ( resolution, retcorner, cb.data )

  elif dataoption==AR_TIGHTCUTOUT:

    # determine if it is a compound type (NEURON) and get the list of relevant segments
    if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
      dataids = db.getChildren ( annoid ) 
    else:
      dataids = [anno.annid]

    # get the bounding box from the index
    bbcorner, bbdim = db.getBoundingBox ( dataids, resolution )

    # figure out which ids are in object
    if bbcorner != None:
      if bbdim[0]*bbdim[1]*bbdim[2] >= 1024*1024*256:
        logger.warning ("Cutout region is inappropriately large.  Dimension: %s,%s,%s" % (bbdim[0],bbdim[1],bbdim[2]))
        raise OCPCAError ("Cutout region is inappropriately large.  Dimension: %s,%s,%s" % (bbdim[0],bbdim[1],bbdim[2]))

    # Call the cuboids interface to get the minimum amount of data
    if anno.__class__ == annotation.AnnNeuron:
      offsets = db.annoCubeOffsets(dataids, resolution, annoid)
    else:
      offsets = db.annoCubeOffsets([annoid], resolution)

    datacuboid = None

    # get a list of indexes in XYZ space
    # for each cube in the index, add it to the data cube
    for (offset,cbdata) in offsets:
      if datacuboid == None:
        datacuboid = np.zeros ( (bbdim[2],bbdim[1],bbdim[0]), dtype=cbdata.dtype )

      datacuboid [ offset[2]-bbcorner[2]:offset[2]-bbcorner[2]+cbdata.shape[0], offset[1]-bbcorner[1]:offset[1]-bbcorner[1]+cbdata.shape[1], offset[0]-bbcorner[0]:offset[0]-bbcorner[0]+cbdata.shape[2] ]  = cbdata

    h5anno.addCutout ( resolution, bbcorner, datacuboid )

  elif dataoption==AR_BOUNDINGBOX:

    # determine if it is a compound type (NEURON) and get the list of relevant segments
    if anno.__class__ in [ annotation.AnnNeuron ] and dataoption != AR_NODATA:
      dataids = db.getChildren ( annoid ) 
    else:
      dataids = [anno.annid]

    bbcorner, bbdim = db.getBoundingBox ( dataids, resolution )
    h5anno.addBoundingBox ( resolution, bbcorner, bbdim )

  # populate with a minimal list of cuboids
  elif dataoption==AR_CUBOIDS:

  #CUBOIDS don't work at zoom resolution
  
    h5anno.mkCuboidGroup()

    if anno.__class__ == annotation.AnnNeuron:
      offsets = db.annoCubeOffsets(dataids, resolution, annoid)
    else:
      offsets = db.annoCubeOffsets([annoid], resolution)

    # get a list of indexes in XYZ space
    # for each cube in the index, add it to the hdf5 file
    for (offset,cbdata) in offsets:
      h5anno.addCuboid ( offset, cbdata )


def getAnnotation ( webargs ):
  """Fetch a RAMON object as HDF5 by object identifier"""

  [ token, sym, otherargs ] = webargs.partition ('/')

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Split the URL and get the args
    args = otherargs.split('/', 2)

    # Make the HDF5 file
    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile()
    h5f = h5py.File ( tmpfile.name,"w" )

    try: 

      db.startTxn ()
    
      # if the first argument is numeric.  it is an annoid
      if re.match ( '^[\d,]+$', args[0] ): 

        annoids = map(int, args[0].split(','))

        for annoid in annoids: 

          # if it's a compoun data type (NEURON) get the list of data ids
          # default is no data
          if args[1] == '' or args[1] == 'nodata':
            dataoption = AR_NODATA
            getAnnoById ( annoid, h5f, proj, db, dataoption )
    
          # if you want voxels you either requested the resolution id/voxels/resolution
          #  or you get data from the default resolution
          elif args[1] == 'voxels':
            dataoption = AR_VOXELS

            try:
              [resstr, sym, rest] = args[2].partition('/')
              resolution = int(resstr) 
            except:
              logger.warning ( "Improperly formatted voxel arguments {}".format(args[2]))
              raise OCPCAError("Improperly formatted voxel arguments {}".format(args[2]))

    
            getAnnoById ( annoid, h5f, proj, db, dataoption, resolution )

          #  or you get data from the default resolution
          elif args[1] == 'cuboids':
            dataoption = AR_CUBOIDS
            try:
              [resstr, sym, rest] = args[2].partition('/')
              resolution = int(resstr) 
            except:
              logger.warning ( "Improperly formatted cuboids arguments {}".format(args[2]))
              raise OCPCAError("Improperly formatted cuboids arguments {}".format(args[2]))
    
            getAnnoById ( annoid, h5f, proj, db, dataoption, resolution )
    
          elif args[1] =='cutout':
    
            # if there are no args or only resolution, it's a tight cutout request
            if args[2] == '' or re.match('^\d+[\w\/]*$', args[2]):
              dataoption = AR_TIGHTCUTOUT
              try:
                [resstr, sym, rest] = args[2].partition('/')
                resolution = int(resstr) 
              except:
                logger.warning ( "Improperly formatted cutout arguments {}".format(args[2]))
                raise OCPCAError("Improperly formatted cutout arguments {}".format(args[2]))

              getAnnoById ( annoid, h5f, proj, db, dataoption, resolution )
    
            else:

              dataoption = AR_CUTOUT
    
              # Perform argument processing
              brargs = restargs.BrainRestArgs ();
              brargs.cutoutArgs ( args[2], proj.datasetcfg )
    
              # Extract the relevant values
              corner = brargs.getCorner()
              dim = brargs.getDim()
              resolution = brargs.getResolution()
    
              getAnnoById ( annoid, h5f, proj, db, dataoption, resolution, corner, dim )
    
          elif args[1] == 'boundingbox':
    
            dataoption = AR_BOUNDINGBOX
            try:
              [resstr, sym, rest] = args[2].partition('/')
              resolution = int(resstr) 
            except:
              logger.warning ( "Improperly formatted bounding box arguments {}".format(args[2]))
              raise OCPCAError("Improperly formatted bounding box arguments {}".format(args[2]))
        
            getAnnoById ( annoid, h5f, proj, db, dataoption, resolution )
    
          else:
            logger.warning ("Fetch identifier %s.  Error: no such data option %s " % ( annoid, args[1] ))
            raise OCPCAError ("Fetch identifier %s.  Error: no such data option %s " % ( annoid, args[1] ))
    
      # the first argument is not numeric.  it is a service other than getAnnotation
      else:
        logger.warning("Get interface %s requested.  Illegal or not implemented. Args: %s" % ( args[0], webargs ))
        raise OCPCAError ("Get interface %s requested.  Illegal or not implemented" % ( args[0] ))
    
    # Close the file on a error: it won't get closed by the Web server
    except: 
      db.rollback()
      tmpfile.close()
      h5f.close()
      raise

    # Close the HDF5 file always
    h5f.flush()
    h5f.close()
    db.commit()

    # Return the HDF5 file
    tmpfile.seek(0)
    return tmpfile.read()


def getCSV ( webargs ):
  """Fetch a RAMON object as CSV.  Always includes bounding box.  No data option."""

  [ token, csvliteral, annoid, reststr ] = webargs.split ('/',3)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Make the HDF5 file
    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile()
    h5f = h5py.File ( tmpfile.name )

    try:

      dataoption = AR_BOUNDINGBOX
      try:
        [resstr, sym, rest] = reststr.partition('/')
        resolution = int(resstr) 
      except:
        logger.warning ( "Improperly formatted cutout arguments {}".format(reststr))
        raise OCPCAError("Improperly formatted cutout arguments {}".format(reststr))

      
      getAnnoById ( annoid, h5f, proj, db, dataoption, resolution )

      # convert the HDF5 file to csv
      csvstr = h5ann.h5toCSV ( h5f )

    finally:
      h5f.close()
      tmpfile.close()

  return csvstr 


def getAnnotations ( webargs, postdata ):
  """Get multiple annotations.  Takes an HDF5 that lists ids in the post."""

  [ token, objectsliteral, otherargs ] = webargs.split ('/',2)

  # Get the annotation database
  [ db, proj, projdb ] = loadDBProj ( token )

  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )
  
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
  
    # Read the post data HDF5 and get a list of identifiers
    tmpinfile = tempfile.NamedTemporaryFile ( )
    tmpinfile.write ( postdata )
    tmpinfile.seek(0)
    h5in = h5py.File ( tmpinfile.name )

    try:

      # IDENTIFIERS
      if not h5in.get('ANNOIDS'):
        logger.warning ("Requesting multiple annotations.  But no HDF5 \'ANNOIDS\' field specified.") 
        raise OCPCAError ("Requesting multiple annotations.  But no HDF5 \'ANNOIDS\' field specified.") 

      # GET the data out of the HDF5 file.  Never operate on the data in place.
      annoids = h5in['ANNOIDS'][:]

      # set variables to None: need them in call to getAnnoByID, but not all paths set all
      corner = None
      dim = None
      resolution = None
      dataarg = ''

      # process options
      # Split the URL and get the args
      if otherargs != '':
        ( dataarg, cutout ) = otherargs.split('/', 1)

      if dataarg =='' or dataarg == 'nodata':
        dataoption = AR_NODATA

      elif dataarg == 'voxels':
        dataoption = AR_VOXELS
        # only arg to voxels is resolution
        try:
          [resstr, sym, rest] = cutout.partition('/')
          resolution = int(resstr) 
        except:
          logger.warning ( "Improperly formatted voxel arguments {}".format(cutout))
          raise OCPCAError("Improperly formatted voxel arguments {}".format(cutout))


      elif dataarg == 'cutout':
        # if blank of just resolution then a tightcutout
        if cutout == '' or re.match('^\d+[\/]*$', cutout):
          dataoption = AR_TIGHTCUTOUT
          try:
            [resstr, sym, rest] = cutout.partition('/')
            resolution = int(resstr) 
          except:
            logger.warning ( "Improperly formatted cutout arguments {}".format(cutout))
            raise OCPCAError("Improperly formatted cutout arguments {}".format(cutout))
        else:
          dataoption = AR_CUTOUT

          # Perform argument processing
          brargs = restargs.BrainRestArgs ();
          brargs.cutoutArgs ( cutout, proj.datsetcfg )

          # Extract the relevant values
          corner = brargs.getCorner()
          dim = brargs.getDim()
          resolution = brargs.getResolution()

      # RBTODO test this interface
      elif dataarg == 'boundingbox':
        # if blank of just resolution then a tightcutout
        if cutout == '' or re.match('^\d+[\/]*$', cutout):
          dataoption = AR_BOUNDINGBOX
          try:
            [resstr, sym, rest] = cutout.partition('/')
            resolution = int(resstr) 
          except:
            logger.warning ( "Improperly formatted bounding box arguments {}".format(cutout))
            raise OCPCAError("Improperly formatted bounding box arguments {}".format(cutout))

      else:
          logger.warning ("In getAnnotations: Error: no such data option %s " % ( dataarg ))
          raise OCPCAError ("In getAnnotations: Error: no such data option %s " % ( dataarg ))

      try:

        # Make the HDF5 output file
        # Create an in-memory HDF5 file
        tmpoutfile = tempfile.NamedTemporaryFile()
        h5fout = h5py.File ( tmpoutfile.name )

        # get annotations for each identifier
        for annoid in annoids:
          # the int here is to prevent using a numpy value in an inner loop.  This is a 10x performance gain.
          getAnnoById ( int(annoid), h5fout, proj, db, dataoption, resolution, corner, dim )

      except:
        h5fout.close()
        tmpoutfile.close()

    finally:
      # close temporary file
      h5in.close()
      tmpinfile.close()

    # Transmit back the populated HDF5 file
    h5fout.flush()
    h5fout.close()
    tmpoutfile.seek(0)
    return tmpoutfile.read()

def putAnnotationAsync ( webargs, postdata ):
  """Put a RAMON object asynchrously as HDF5 by object identifier"""
  
  [ token, sym, optionsargs ] = webargs.partition ('/')
  options = optionsargs.split('/')

  import anydbm
  import time
  any_db = anydbm.open( ocpcaprivate.ssd_log_location+ocpcaprivate.bsd_name, 'c', 0777)

  print "Wrting Data to SSD"

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # Don't write to readonly projects
  if proj.getReadOnly()==1:
    logger.warning("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
    raise OCPCAError("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
  (fd,filename) = tempfile.mkstemp(suffix=".hdf5", prefix=token, dir=ocpcaprivate.ssd_log_location)
  os.close(fd)
  try:
    fd = os.open(filename ,os.O_CREAT | os.O_WRONLY | os.O_NOATIME | os.O_SYNC )
    os.write ( fd, postdata )
    os.close( fd )
    metadata = ( token, time.time(), optionsargs )
    any_db[ str(filename) ] = "{}".format( metadata )
  except Exception, e:
    print e
  
  from ocpca.tasks import async

  #async.delay()
  #async.apply_async(countdown=5)

  # TODO KL - celery to rewrite data
  #import h5annasync
  #h5annasync.h5Async( token, optionsargs )


def putAnnotation ( webargs, postdata ):
  """Put a RAMON object as HDF5 by object identifier"""

  [ token, sym, optionsargs ] = webargs.partition ('/')

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Don't write to readonly projects
    if proj.getReadOnly()==1:
      logger.warning("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))
      raise OCPCAError("Attempt to write to read only project. %s: %s" % (proj.getDBName(),webargs))

    options = optionsargs.split('/')

    # return string of id values
    retvals = [] 

    # Make a named temporary file for the HDF5
    tmpfile = tempfile.NamedTemporaryFile ( )
    tmpfile.write ( postdata )
    tmpfile.seek(0)
    h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

    try:

      for k in h5f.keys():
        
        idgrp = h5f.get(k)

        # Convert HDF5 to annotation
        anno = h5ann.H5toAnnotation ( k, idgrp, db )

        # set the identifier (separate transaction)
        if not ('update' in options or 'dataonly' in options or 'reduce' in options):
          anno.setID ( db )

        # start a transaction: get mysql out of line at a time mode
        db.startTxn ()

        tries = 0 
        done = False
        while not done and tries < 5:

          try:

            if anno.__class__ in [ annotation.AnnNeuron, annotation.AnnSeed ] and ( idgrp.get('VOXELS') or idgrp.get('CUTOUT')):
              logger.warning ("Cannot write to annotation type %s" % (anno.__class__))
              raise OCPCAError ("Cannot write to annotation type %s" % (anno.__class__))

            if 'update' in options and 'dataonly' in options:
              logger.warning ("Illegal combination of options. Cannot use udpate and dataonly together")
              raise OCPCAError ("Illegal combination of options. Cannot use udpate and dataonly together")

            elif not 'dataonly' in options and not 'reduce' in options:

              # Put into the database
              db.putAnnotation ( anno, options )

            #  Get the resolution if it's specified
            if 'RESOLUTION' in idgrp:
              resolution = int(idgrp.get('RESOLUTION')[0])

            # Load the data associated with this annotation
            #  Is it voxel data?
            if 'VOXELS' in idgrp:
              voxels = np.array(idgrp.get('VOXELS'),dtype=np.uint32)
            else: 
              voxels = None

            if voxels!=None and 'reduce' not in options:

              if 'preserve' in options:
                conflictopt = 'P'
              elif 'exception' in options:
                conflictopt = 'E'
              else:
                conflictopt = 'O'

              # Check that the voxels have a conforming size:
              if voxels.shape[1] != 3:
                logger.warning ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
                raise OCPCAError ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))

              exceptions = db.annotate ( anno.annid, resolution, voxels, conflictopt )

            # Otherwise this is a shave operation
            elif voxels != None and 'reduce' in options:

              # Check that the voxels have a conforming size:
              if voxels.shape[1] != 3:
                logger.warning ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
                raise OCPCAError ("Voxels data not the right shape.  Must be (:,3).  Shape is %s" % str(voxels.shape))
              db.shave ( anno.annid, resolution, voxels )

            # Is it dense data?
            if 'CUTOUT' in idgrp:
              cutout = np.array(idgrp.get('CUTOUT'),dtype=np.uint32)
            else:
              cutout = None
            if 'XYZOFFSET' in idgrp:
              h5xyzoffset = idgrp.get('XYZOFFSET')
            else:
              h5xyzoffset = None

            if cutout != None and h5xyzoffset != None and 'reduce' not in options:

              if 'preserve' in options:
                conflictopt = 'P'
              elif 'exception' in options:
                conflictopt = 'E'
              else:
                conflictopt = 'O'

              #  the zstart in datasetcfg is sometimes offset to make it aligned.
              #   Probably remove the offset is the best idea.  and align data
              #    to zero regardless of where it starts.  For now.
              corner = h5xyzoffset[:] 
              corner[2] -= proj.datasetcfg.slicerange[0]

              db.annotateEntityDense ( anno.annid, corner, resolution, np.array(cutout), conflictopt )

            elif cutout != None and h5xyzoffset != None and 'reduce' in options:

              corner = h5xyzoffset[:] 
              corner[2] -= proj.datasetcfg.slicerange[0]

              db.shaveEntityDense ( anno.annid, corner, resolution, np.array(cutout))

            elif cutout != None or h5xyzoffset != None:
              #TODO this is a loggable error
              pass


            # only add the identifier if you commit
            if not 'dataonly' in options and not 'reduce' in options:
              retvals.append(anno.annid)

            # Here with no error is successful
            done = True

          # rollback if you catch an error
          except MySQLdb.OperationalError, e:
            logger.warning (" Put Anntotation: Transaction did not complete. %s" % (e))
            tries += 1
            db.rollback()
            continue
          except MySQLdb.Error, e:
            logger.warning ("Put Annotation: Put transaction rollback. %s" % (e))
            db.rollback()
            raise
          except Exception, e:
            logger.exception ("Put Annotation:Put transaction rollback. %s" % (e))
            db.rollback()
            raise

          # Commit if there is no error
          db.commit()

    finally:
      h5f.close()
      tmpfile.close()


    retstr = ','.join(map(str, retvals))

    # return the identifier
    return retstr


#  Return a list of annotation object IDs
#  for now by type and status
def queryAnnoObjects ( webargs, postdata=None ):
  """ Return a list of anno ids restricted by equality predicates.
      Equalities are alternating in field/value in the url.
  """

  [ token, dontuse, restargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    annoids = db.getAnnoObjects ( restargs.split('/') )

    # We have a cutout as well
    if postdata:

    # RB this is a brute force implementation.  This probably needs to be
    #  optimized to use several different execution strategies based on the
    #  cutout size and the number of objects.

      # Make a named temporary file for the HDF5
      tmpfile = tempfile.NamedTemporaryFile ( )
      tmpfile.write ( postdata )
      tmpfile.seek(0)
      h5f = h5py.File ( tmpfile.name, driver='core', backing_store=False )

      try:


        corner = h5f['XYZOFFSET'][:]
        dim = h5f['CUTOUTSIZE'][:]
        resolution = h5f['RESOLUTION'][0]

        if not proj.datasetcfg.checkCube( resolution, corner[0], corner[0]+dim[0], corner[1], corner[1]+dim[1], corner[2], corner[2]+dim[2] ):
          logger.warning ( "Illegal cutout corner=%s, dim=%s" % ( corner, dim))
          raise OCPCAError ( "Illegal cutout corner=%s, dim=%s" % ( corner, dim))

        # RBFIX this a hack
        #
        #  the zstart in datasetcfg is sometimes offset to make it aligned.
        #   Probably remove the offset is the best idea.  and align data
        #    to zero regardless of where it starts.  For now.
        corner[2] -= proj.datasetcfg.slicerange[0]

        cutout = db.cutout ( corner, dim, resolution )
        annoids = np.intersect1d ( annoids, np.unique( cutout.data ))

      finally:

        h5f.close()
        tmpfile.close()

  return h5ann.PackageIDs ( annoids ) 


def deleteAnnotation ( webargs ):
  """Delete a RAMON object"""

  [ token, sym, otherargs ] = webargs.partition ('/')

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
  
    # Don't write to readonly projects                                                                                                                                          
    if proj.getReadOnly()==1:
      logger.warning("Attempt to delete from a read only project. %s: %s" % (proj.getDBName(),webargs))
      raise OCPCAError("Attempt to delete from a  read only project. %s: %s" % (proj.getDBName(),webargs))

    # Split the URL and get the args
    args = otherargs.split('/', 2)

    # if the first argument is numeric.  it is an annoid
    if re.match ( '^[\d,]+$', args[0] ): 
      annoids = map(int, args[0].split(','))
    # if not..this is not a well-formed delete request
    else:
      logger.warning ("Delete did not specify a legal object identifier = %s" % args[0] )
      raise OCPCAError ("Delete did not specify a legal object identifier = %s" % args[0] )

    for annoid in annoids: 

      db.startTxn()
      tries = 0
      done = False
      while not done and tries < 5:

        try:
          db.deleteAnnotation ( annoid )
          done = True
        # rollback if you catch an error
        except MySQLdb.OperationalError, e:
          logger.warning ("Transaction did not complete. %s" % (e))
          tries += 1
          db.rollback()
          continue
        except MySQLdb.Error, e:
          logger.warning ("Put transaction rollback. %s" % (e))
          db.rollback()
          raise
        except Exception, e:
          logger.exception ("Put transaction rollback. %s" % (e))
          db.rollback()
          raise

        db.commit()


def jsonInfo ( webargs ):
  """Return project information in json format"""

  [ token, projinfoliteral, otherargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    import jsonprojinfo
    return jsonprojinfo.jsonInfo( proj, db )


def projInfo ( webargs ):

  [ token, projinfoliteral, otherargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Create an in-memory HDF5 file
    tmpfile = tempfile.NamedTemporaryFile ()
    h5f = h5py.File ( tmpfile.name )

    try:

      # Populate the file with project information
      h5projinfo.h5Info ( proj, db, h5f ) 

    finally:
      h5f.close()
      tmpfile.seek(0)

    return tmpfile.read()


def chanInfo ( webargs ):
  """Return information about the project's channels"""

  [ token, projinfoliteral, otherargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    import jsonprojinfo
    return jsonprojinfo.jsonChanInfo( proj, db )


def mcfcPNG ( proj, db, token, service, chanstr, imageargs ):
  """Inner part of mcFalseColor returns and PNG file"""

  if proj.getDBType() != ocpcaproj.CHANNELS_16bit and proj.getDBType() != ocpcaproj.CHANNELS_8bit:
    logger.warning ( "Not a multiple channel project." )
    raise OCPCAError ( "Not a multiple channel project." )

  channels = chanstr.split(",")

  # make sure that the channels are ints
  chanobj = ocpcachannel.OCPCAChannels ( db )
  channels = chanobj.rewriteToInts ( channels )
  (startwindow, endwindow) = proj.datasetcfg.windowrange


  combined_img = None

  for i in range(len(channels)):
     
    # skip 0 channels
    if channels[i]==0:
      continue
       
    if service == 'xy':
      cb = xySlice ( str(channels[i]) + "/" + imageargs, proj, db )
    elif service == 'xz':
      cb = xzSlice ( str(channels[i]) + "/" + imageargs, proj, db )
    elif service == 'yz':
      cb = yzSlice ( str(channels[i]) + "/" + imageargs, proj, db )
    else:
      logger.warning ( "No such service %s. Args: %s" % (service,webargs))
      raise OCPCAError ( "No such service %s" % (service) )

    # reduction factor
    scaleby = 1.0
    if proj.getDBType() == ocpcaproj.CHANNELS_8bit:
      scaleby = 1
    elif proj.getDBType() == ocpcaproj.CHANNELS_16bit and ( startwindow==0 and endwindow==0):
      scaleby = 1.0/256
    elif proj.getDBType() == ocpcaproj.CHANNELS_16bit and ( endwindow!=0 ):
      scaleby = 1

    # First channel is cyan
    if i == 0:
      data32 = np.array ( cb.data * scaleby, dtype=np.uint32 )
      combined_img = np.left_shift(data32,8) + np.left_shift(data32,16)
    # Second is Magenta
    elif i == 1:
      data32 = np.array ( cb.data * scaleby, dtype=np.uint32 )
      combined_img +=  np.left_shift(data32,16) + data32 
    # THird is yellow
    elif i == 2:  
      data32 = np.array ( cb.data * scaleby, dtype=np.uint32 )
      combined_img +=  np.left_shift(data32,8) + data32 
    # Fourth is Red
    elif i == 3:
      data32 = np.array ( cb.data * scaleby, dtype=np.uint32 )
      combined_img +=  data32 
    # Fifth is Green
    elif i == 4:
      data32 = np.array ( cb.data * scaleby, dtype=np.uint32 )
      combined_img += np.left_shift(data32,8)
    # Sixth is Blue
    elif i == 5:
      data32 = np.array ( cb.data * scaleby, dtype=np.uint32 )
      combined_img +=  np.left_shift(data32,16) 
    else:
      logger.warning ( "Only support six channels at a time.  You requested %s " % (chanstr))
      raise OCPCAError ( "Only support six channels at a time.  You requested %s " % (chanstr))

    # Set the alpha channel only for nonzero pixels
    combined_img = np.where ( combined_img > 0, combined_img + 0xFF000000, 0 )
    
  if service == 'xy':
    ydim, xdim = combined_img.shape[1:3]
    outimage = Image.frombuffer ( 'RGBA', (xdim,ydim), combined_img[0,:,:].flatten(), 'raw', 'RGBA', 0, 1 ) 
  elif service == 'xz':
    ydim = combined_img.shape[0]
    xdim = combined_img.shape[2]
    outimage = Image.frombuffer ( 'RGBA', (xdim,ydim), combined_img[:,0,:].flatten(), 'raw', 'RGBA', 0, 1 ) 
  elif service == 'yz':
    ydim = combined_img.shape[0]
    xdim = combined_img.shape[1]
    outimage = Image.frombuffer ( 'RGBA', (xdim,ydim), combined_img[:,:,0].flatten(), 'raw', 'RGBA', 0, 1 ) 

  # Enhance the image
  if startwindow==0 and endwindow==0:
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Brightness(outimage)
    outimage = enhancer.enhance(4.0)
  
  return outimage


def mcFalseColor ( webargs ):
  """False color image of multiple channels"""

  [ token, mcfcstr, service, chanstr, imageargs ] = webargs.split ('/', 4)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:
    outimage = mcfcPNG ( proj, db,  token, service, chanstr, imageargs )

  fileobj = cStringIO.StringIO ( )
  outimage.save ( fileobj, "PNG" )

  fileobj.seek(0)
  return fileobj.read()


def reserve ( webargs ):
  """Reserve annotation ids"""

  [ token, reservestr, cnt, other ] = webargs.split ('/', 3)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    if proj.getDBType() != ocpcaproj.ANNOTATIONS and proj.getDBType() != ocpcaproj.ANNOTATIONS_64bit: 
      raise OCPCAError ("Illegal project type for reserve.")

    try:
      count = int(cnt)
    except:
      raise OCPCAError ("Illegal arguments to reserve: {}".format(webargs))

    # perform the reservation
    firstid = db.reserve ( int(cnt))

    return json.dumps ( (firstid, int(cnt)) )



def getField ( webargs ):
  """Return a single HDF5 field"""

  try:
    [ token, annid, verb, field, rest ] = webargs.split ('/',4)
  except:
    logger.warning("Illegal getField request.  Wrong number of arguments.")
    raise OCPCAError("Illegal getField request.  Wrong number of arguments.")

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # retrieve the annotation 
    anno = db.getAnnotation ( annid )

  if anno == None:
    logger.warning("No annotation found at identifier = %s" % (annoid))
    raise OCPCAError ("No annotation found at identifier = %s" % (annoid))

  value = anno.getField ( field )
  return value


def setField ( webargs ):
  """Assign a single HDF5 field"""

  # RBTODO this should call setField in ocpcadb.  Not here.

  try:
    [ token, annid, verb, field, value, rest ] = webargs.split ('/',5)
  except:
    logger.warning("Illegal getField request.  Wrong number of arguments.")
    raise OCPCAError("Illegal getField request.  Wrong number of arguments.")
    
  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    db.startTxn()
    
    try:

      # retrieve the annotation 
      anno = db.getAnnotation ( annid )
      if anno == None:
        logger.warning("No annotation found at identifier = %s" % (annid))
        raise OCPCAError ("No annotation found at identifier = %s" % (annid))

      anno.setField ( field, value )
      anno.update ( db.cursor )

    except:
      db.rollback()
      raise

    db.commit()



def merge ( webargs ):
  """Return a single HDF5 field"""
  
  try:
    [token, service, relabelids, rest] = webargs.split ('/',3)
  except:
    logger.warning("Illegal globalMerge request.  Wrong number of arguments.")
    raise OCPCAError("Illegal globalMerber request.  Wrong number of arguments.")
  
  # get the ids from the list of ids and store it in a list vairable
  ids = relabelids.split(',')
  last_id = len(ids)-1
  ids[last_id] = ids[last_id].replace("/","")
  
  # Make ids a numpy array to speed vectorize
  ids = np.array(ids,dtype=np.uint32)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    #mergetype = rest
    [mergetype,resolution] = rest.split('/',1)
    if mergetype == "global":
      if resolution != '':
        [resolution,extra] = resolution.split('/')
      return db.mergeGlobal(ids, mergetype, resolution)
    else:
      [mergetype, imageargs] = mergetype.split ('/',1)
      print mergetype
      
      if mergetype == "2D":
        slicenum = imageargs.strip('/')
        return db.merge2D(ids, mergetype, 1, slicenum)
    
      elif mergetype == "3D":
        # 3d merge 
        imageargs = "1/"+ imageargs
        print imageargs
        # Perform argument processing for the bounding box
        try:
          args = restargs.BrainRestArgs ();
          args.mergeArgs ( imageargs, proj.datasetcfg )
        except restargs.RESTArgsError, e:
          logger.warning("REST Arguments %s failed: %s" % (imageargs,e))
          raise OCPCAError(e)
        # Extract the relevant values
        corner = args.getCorner()
        dim = args.getDim()
        resolution = args.getResolution()
        
        print corner
        print dim
        print resolution
        
        # Perform the relabeling
       # cube = db.cutout ( corner, dim, resolution, channel )
      

        return db.merge3D(ids,corner, dim, resolution)
      else:
        return "Invalid Merge Type : Select global, 2D or 3D"
  
  
def publicTokens ( self ):
  """Return a json formatted list of public tokens"""
  
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:

    import jsonprojinfo
    return jsonprojinfo.publicTokens ( projdb )


#
#  exceptions: list of multiply defined voxels in a cutout
#
def exceptions ( webargs, ):
  """list of multiply defined voxels in a cutout"""

  [ token, exceptliteral, cutoutargs ] = webargs.split ('/',2)

  # pattern for using contexts to close databases
  # get the project 
  with closing ( ocpcaproj.OCPCAProjectsDB() ) as projdb:
    proj = projdb.loadProject ( token )

  # and the database and then call the db function
  with closing ( ocpcadb.OCPCADB(proj) ) as db:

    # Perform argument processing
    try:
      args = restargs.BrainRestArgs ();
      args.cutoutArgs ( cutoutargs, proj.datasetcfg )
    except restargs.RESTArgsError, e:
      logger.warning("REST Arguments %s failed: %s" % (webargs,e))
      raise OCPCAError(e)

    # Extract the relevant values
    corner = args.getCorner()
    dim = args.getDim()
    resolution = args.getResolution()

    # check to make sure it's an annotation project
    if proj.getDBType() != ocpcaproj.ANNOTATIONS and proj.getDBType() != ocpcaproj.ANNOTATIONS_64bit: 
      logger.warning("Asked for exceptions on project that is not of type ANNOTATIONS")
      raise OCPCAError("Asked for exceptions on project that is not of type ANNOTATIONS")
    elif not proj.getExceptions():
      logger.warning("Asked for exceptions on project without exceptions")
      raise OCPCAError("Asked for exceptions on project without exceptions")
      
    # Get the exceptions -- expect a rect np.array of shape x,y,z,id1,id2,...,idn where n is the longest exception list
    exceptions = db.exceptionsCutout ( corner, dim, resolution )

    # package as an HDF5 file
    tmpfile = tempfile.NamedTemporaryFile ()
    fh5out = h5py.File ( tmpfile.name )

    try:

      # empty HDF5 file if exceptions = None
      if exceptions == None:
        ds = fh5out.create_dataset ( "exceptions", (3,), np.uint8 )
      else:
        ds = fh5out.create_dataset ( "exceptions", tuple(exceptions.shape), exceptions.dtype, compression='gzip', data=exceptions )

    except:
      fh5out.close()
      tmpfile.close()
      raise

    fh5out.close()
    tmpfile.seek(0)
    return tmpfile.read()
