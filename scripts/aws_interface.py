# -*- coding: utf-8 -*-

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

import os
import sys
from contextlib import closing
import argparse
import blosc
from operator import mul
import csv

sys.path += [os.path.abspath('../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
import django
django.setup()
from django.conf import settings

import ndlib
from cube import Cube
from ndtype import *
import ndproj
import spatialdb
from s3io import S3IO
from nddynamo.cuboidindexdb import CuboidIndexDB
from ndbucket.cuboidbucket import CuboidBucket
from s3util import generateS3BucketName, generateS3Key


class AwsInterface:

  def __init__(self, token, channel_name, resolution):
    """Create the bucket and intialize values"""
  
    self.token = token
    self.channel_name = channel_name
    self.resolution = resolution
    
    with closing (ndproj.NDProjectsDB()) as projdb:
      self.proj = projdb.loadToken(self.token)
    
    with closing (spatialdb.SpatialDB(self.proj)) as self.db:
      # create the s3 I/O and index objects
      self.s3_io = S3IO(self.db)
      self.cuboid_db = CuboidBucket()
      self.cuboidindex_db = CuboidIndexDB(self.proj.getProjectName(), self.channel_name)
      # self.file_type = result.file_type
      # self.tile_size = result.tile_size
      # self.data_location = result.data_location
      # self.url = result.url
  
  def deleteProject(self):
    """Delete the project"""

    for item in self.cuboidindex_db.queryProjectItems():
      self.cuboid_bucket.deleteObject(item['supercuboid_key'])
      self.cuboidindex_db.deleteItem(item['supercuboid_key'])
  
  
  def deleteChannel(self):
    """Delete the channel"""

    for item in self.cuboidindex_db.queryChannelItems():
      self.cuboid_bucket.deleteObject(item['supercuboid_key'])
      self.cuboidindex_db.deleteItem(item['supercuboid_key'])


  def deleteResolution(self, resolution):
    """Delete an existing resolution"""
    
    for item in self.cuboidindex_db.queryResolutionItems(resolution):
      self.cuboid_bucket.deleteObject(item['supercuboid_key'])
      self.cuboidindex_db.deleteItem(item['supercuboid_key'])

  
  def uploadExistingProject(self):
    """Upload an existing project to S3"""

    with closing (ndproj.NDProjectsDB()) as projdb:
      proj = projdb.loadToken(self.token)
    
    with closing (spatialdb.SpatialDB(proj)) as db:
      # creating the channel obj
      ch = proj.getChannelObj(self.channel_name)
      
      # ingest 1 or more resolutions based on user input
      if self.resolution is None:
        stop_res = ch.getResolution()
        start_res = proj.datasetcfg.scalinglevels
      else:
        start_res = self.resolution
        stop_res = self.resolution - 1
      
      # iterating over resolution
      for cur_res in range(start_res, stop_res, -1):
        
        # get the source database sizes
        [[x_imagesz, y_imagesz, z_imagesz], time_range] = proj.datasetcfg.imageSize(cur_res)
        [x_cubedim, y_cubedim, z_cubedim] = cubedim = proj.datasetcfg.getCubeDims()[cur_res]
        [x_offset, y_offset, z_offset] = proj.datasetcfg.getOffset()[cur_res]

        [x_supercubedim, y_supercubedim, z_supercubedim] = supercubedim = map(mul, cubedim, SUPERCUBESIZE)

        # set the limits for iteration on the number of cubes in each dimension
        x_limit = (x_imagesz-1) / (x_supercubedim) + 1
        y_limit = (y_imagesz-1) / (y_supercubedim) + 1
        z_limit = (z_imagesz-1) / (z_supercubedim) + 1

        for z in range(z_limit):
          for y in range(y_limit):
            for x in range(x_limit):

              try:
                # cutout the data at the current resolution
                data = db.cutout(ch, [x*x_supercubedim, y*y_supercubedim, z*z_supercubedim], [x_supercubedim, y_supercubedim, z_supercubedim], cur_res).data
                # generate the morton index
                morton_index = ndlib.XYZMorton([x, y, z])

                print "Inserting Cube {} at res {}".format(morton_index, cur_res), [x,y,z]
                # updating the index
                self.cuboidindex_db.putItem(cur_res, x, y, z)
                # inserting the cube
                self.s3_io.putCube(ch, cur_res, morton_index, blosc.pack_array(data))
              
              except Exception as e:
                # checkpoint the ingest
                self.checkpoint_ingest(cur_res, x, y, z, e)
                raise e
  

  def checkpoint_ingest(self, resolution, x, y, z, e, time=0):
    """Checkpoint the progress to file"""
    
    with closing(open('checkpoint_ingest.csv', 'wb')) as csv_file:
      field_names = ['project_name', 'channel_name', 'resolution', 'x', 'y', 'z', 'time', 'exception']
      csv_writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=field_names)
      csv_writer.writeheader()
      csv_writer.writerow({'project_name' : self.proj.getProjectName(), 'channel_name' : self.channel_name, 'resolution' : resolution, 'x' : x, 'y' : y, 'z' : z, 'time' : time, 'exception' : e.message})

  
  def load_checkpoint(self):
    """Load from a checkpoint file"""
    return NotImplemented

def main():
  
  parser = argparse.ArgumentParser(description="Upload an existing project of NeuroData to s3")
  parser.add_argument('token', action='store', help='Token for the project')
  parser.add_argument('channel_name', action='store', help='Channel Name in the project')
  parser.add_argument('--res', dest='resolution', action='store', type=int, default=None, help='Resolution to upload')
  # parser.add_argument('--file', dest='file_type', action='store', choices=['tif', 'tiff', 'jpg', 'png'], default='tif', help='File type')
  # parser.add_argument('--new', dest='new_project', action='store', choices=['slice', 'catmaid'], default='slice', help='New Project')
  # parser.add_argument('--tilesz', dest='tile_size', action='store', type=int, default=512, help='Tile Size')
  # parser.add_argument('--data', dest='data_location', action='store', type=str, default='/data/scratch/', help='File Location')
  # parser.add_argument('--url', dest='url', action='store', type=str, help='Http URL')
  result = parser.parse_args()
  
  # TODO KL Make these interfaces which can called from the command line
  aws_interface = AwsInterface(result.token, result.channel_name, result.resolution)
  aws_interface.uploadExistingProject()


if __name__ == '__main__':
  main()
