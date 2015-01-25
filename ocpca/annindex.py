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

import numpy as np
import array
import cStringIO
import tempfile
import h5py
import MySQLdb

import zindex
import ocpcaproj

import logging
logger=logging.getLogger("ocp")

#
#  AnnotateIndex: Maintain the index in the database
# AUTHOR: Priya Manavalan

class AnnotateIndex:

  # Constructor 
  #
   def __init__(self,kvio,proj):
      """Give an active connection.  This puts all index operations in the same transation as the calling db."""

      self.proj = proj
      self.kvio = kvio

      if self.proj.getKVEngine() == 'MySQL':
        self.NPZ = True
      else: 
        self.NPZ = False
   
   #
   # getIndex -- Retrieve the index for the annotation with id
   #
   def getIndex ( self, entityid, resolution, update=False ):

    idxstr = self.kvio.getIndex ( entityid, resolution, update )
    if idxstr:
      if self.NPZ:
        fobj = cStringIO.StringIO ( idxstr )
        return np.load ( fobj )      
      else:
        # cubes are HDF5 files
        with closing (tempfile.NamedTemporaryFile ()) as tmpfile:
          tmpfile.write ( idxstr )
          tmpfile.seek(0)
          h5 = h5py.File ( tmpfile.name ) 
  
          # load the numpy array
          return np.array ( h5['index'] )
    else:
      return []
       
   #
   # putIndex -- Write the index for the annotation with id
   #
   def putIndex ( self, entityid, resolution, index, update=False ):

    if self.NPZ:
      fileobj = cStringIO.StringIO ()
      np.save ( fileobj, index )
      self.kvio.putIndex ( entityid, resolution, fileobj.getvalue(), update )
    else:
#      if index.dtype == np.float64:
#        import pdb; pdb.set_trace()

      with closing ( tempfile.NamedTemporaryFile () ) as tmpfile:
        h5 = h5py.File ( tmpfile.name )
        h5.create_dataset ( "index", tuple(index.shape), index.dtype,
                                 compression='gzip',  data=index )
        h5.close()
        tmpfile.seek(0)
        self.kvio.putIndex ( entityid, resolution, tmpfile.read(), update )

#
# Update Index Dense - Updated the annotation database with the given hash index table
#
   def updateIndexDense(self,index,resolution):
      """Updated the database index table with the input index hash table"""

      for key, value in index.iteritems():
         cubelist = list(value)
         cubeindex=np.array(cubelist, dtype=np.uint64)
          
         curindex = self.getIndex(key,resolution,True)
         
         if curindex==[]:
            self.putIndex ( key, resolution, cubeindex, False )
            
         else:
             #Update index to the union of the currentIndex and the updated index
            newIndex=np.union1d(curindex,cubeindex)
            self.putIndex ( key, resolution, newIndex, True )

   #
   #deleteIndex:
   #   Delete the index for a given annotation id for current resolution
   #
   def deleteIndexResolution(self,annid,resolution):
      """delete the index for a given annid""" 
      
      #delete Index table for each resolution
      sql = "DELETE FROM " +  self.proj.getIdxTable(resolution)  +  " WHERE annid=" + str(annid)
      try:
         self.cursor.execute ( sql )
      except MySQLdb.Error, e:
         logger.error("Error deleting the index %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
         raise
      except:
         logger.exception("Unknown exception In deleteIndexResolution")
         raise


   #deleteIndex:                                                                                                                                                                                       #   Delete the index for a given annotation id                                                                                                                                                      #                                                                                                                                                                                                 
   def deleteIndex(self,annid,resolutions):
      """delete the index for a given annid"""

      #delete Index table for each resolution                                                                                                                                                        
      for res in resolutions:
        self.kvio.deleteIndex(annid,res)

#
# Update Index - Updated the annotation objectwith the given index
#                                                                                                                                                                      
   def updateIndex(self,annid,cubeindex,resolution):
      """Updated the database index table with the input index hash table"""

      curindex = self.getIndex(annid,resolution,True)
      
      if curindex==[]:
         sql = "INSERT INTO " +  self.proj.getIdxTable(resolution)  +  "( annid, cube) VALUES ( %s, %s)"
         
         try:
            fileobj = cStringIO.StringIO ()
            np.save ( fileobj, cubeindex )
            self.cursor.execute ( sql, (annid, fileobj.getvalue()))
         except MySQLdb.Error, e:
            logger.warning("Error updating index %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
            raise
         except BaseException, e:
            logger.exception("Unknown error when updating index")
            raise

      else:
             #Update index to the union of the currentIndex and the updated index                                                                                       
         newIndex=np.union1d(curindex,cubeindex)
             #update index in the database                                                                                                                               
         sql = "UPDATE " + self.proj.getIdxTable(resolution) + " SET cube=(%s) WHERE annid=" + str(annid)
         try:
            fileobj = cStringIO.StringIO ()
            np.save ( fileobj, newIndex )
            self.cursor.execute ( sql, (fileobj.getvalue()))
         except MySQLdb.Error, e:
            logger.warnig("Error updating index %d: %s. sql=%s" % (e.args[0], e.args[1], sql))
            raise
         except:
            logger.exception("Unknown exception")
            raise
