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

import argparse
import sys
import os
from contextlib import closing
import numpy as np
from PIL import Image
import cStringIO
import zlib
import tifffile
import glob

sys.path.append(os.path.abspath('../../django'))
import OCP.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCP.settings'
from django.conf import settings

import django
django.setup()
from ocpuser.models import *

from cube import Cube
import ocpcarest
import ocpcadb
import ocpcaproj
import ocplib

END_WINDOWS = [18603, 19194, 16383, 17391, 18317, 17573, 16383, 18480, 18848, 18711, 18441, 17956, 16383, 18051, 17806, 18893, 19261, 17562, 20017, 18504, 17043, 18083, 17875, 16383]

class Ingest_Data:

  def __init__(self, path, resolution, token_name):
    print "In initialization"
    """ Load image stack into OCP, creating tokens and channels as needed """

    self.token = token_name
    self.resolution = resolution
    self.path = path

    with closing (ocpcaproj.OCPCAProjectsDB()) as projdb:
      self.proj = projdb.loadToken(self.token)
      
      channel_list = glob.glob("{}*.tif".format(self.path))
      channel_list = [i.split('/')[-1].strip('.tif') for i in channel_list]
      channel_list.sort()
      for index, channel_name in enumerate(channel_list):
        self.createChannel(channel_name, index)
        self.ingest(channel_name)

  def createDataset(self):
    """Create a dataset"""

  def createProject(self):
    """Create a project"""

    try:
      existing_proj = Project.objects.get(project_name=self.project_name)
      print "Project {} already exists! Skipping creation of project and token...".format(self.project_name)

    except Project.DoesNotExist, e:
      new_project = Project()
      new_project.project_name = self.project_name
      new_project.user = User.objects.get(id=1)
      new_project.description = "Autogenerated from folder {} using dataset {}".format(self.project_name, self.dataset_name)
      new_project.public = 0
      new_project.dataset = self.dataset
      #new_project.host = 'dsp061.pha.jhu.edu'
      new_project.host = 'localhost'
      new_project.kvengine = 'MySQL'
      #new_project.kvserver = 'dsp061.pha.jhu.edu'
      new_project.kvserver = 'localhost'
      new_project.ocp_version = '0.6'
      new_project.schema_version = '0.6'
      new_project.save()

      pd = ocpcaproj.OCPCAProjectsDB()
      pd.newOCPCAProject(new_project.project_name)

      tk = Token(token_name=new_project.project_name, token_description='Default token for project {}'.format(new_project.project_name), project_id=new_project, public=0, user=new_project.user)
      tk.save()

      self.token = token_name

  def createChannel(self, channel_name, index):
    """ create the channels """

    new_channel = Channel()
    new_channel.project = Project.objects.get(project_name=self.proj.getProjectName())
    new_channel.channel_name = channel_name
    new_channel.channel_description = channel_name
    new_channel.channel_type = 'images'
    new_channel.resolution = self.resolution
    new_channel.propagate = 0
    new_channel.channel_datatype = 'uint16'
    new_channel.readonly = 0
    new_channel.exceptions = 0
    new_channel.startwindow = 0
    new_channel.endwindow = END_WINDOWS[index]
    new_channel.save()

    try:
      # create tables for the channel
      pd = ocpcaproj.OCPCAProjectsDB()
      pd.newOCPCAChannel(self.proj.getProjectName(), new_channel.channel_name)
    except Exception, e:
      print e
      exit()

  def ingest(self, channel_name):
    """ Read image stack and ingest """
    
    # Load a database
    with closing(ocpcaproj.OCPCAProjectsDB()) as projdb:
      proj = projdb.loadToken(self.token)

    with closing(ocpcadb.OCPCADB(proj)) as db:

      ch = proj.getChannelObj(channel_name)
      # get the dataset configuration
      [[ximagesz, yimagesz, zimagesz], (starttime, endtime)] = proj.datasetcfg.imageSize(self.resolution)
      [xcubedim, ycubedim, zcubedim] = cubedim = proj.datasetcfg.getCubeDims()[self.resolution]
      [xoffset, yoffset, zoffset] = proj.datasetcfg.getOffset()[self.resolution]

      # Get a list of the files in the directories
      file_name = "{}{}.tif".format(self.path, channel_name)
      print "Open filename {}".format(file_name)

      imgdata = tifffile.imread(file_name)

      for slice_number in range(zoffset, zimagesz + 1, zcubedim):
        slab = np.zeros([zcubedim, yimagesz, ximagesz], dtype=np.uint32)
        for b in range(zcubedim):
          if (slice_number + b <= zimagesz):

            if (slice_number + b) < zimagesz:

                slab[b, :, :] = imgdata[(slice_number + b), :, :]
            else:
                imgdata = np.zeros((yimagesz, ximagesz), dtype=np.uint32)
                slab[b, :, :] = imgdata

        for y in range(0, yimagesz + 1, ycubedim):
          for x in range(0, ximagesz + 1, xcubedim):

            # Getting a Cube id and ingesting the data one cube at a time
            zidx = ocplib.XYZMorton([x / xcubedim, y / ycubedim, (slice_number - zoffset) / zcubedim])
            cube = Cube.getCube(cubedim, ch.getChannelType(), ch.getDataType())
            cube.zeros()

            xmin = x
            ymin = y
            xmax = min(ximagesz, x + xcubedim)
            ymax = min(yimagesz, y + ycubedim)
            zmin = 0
            zmax = min(slice_number + zcubedim, zimagesz + 1)

            cube.data[0:zmax - zmin, 0:ymax - ymin, 0:xmax - xmin] = slab[zmin:zmax, ymin:ymax, xmin:xmax]
            db.putCube(ch, zidx, self.resolution, cube, update=True)


def main():

  parser = argparse.ArgumentParser(description='Ingest the TIFF data')
  parser.add_argument("path", action="store", type=str, help='Directory with the image files')
  parser.add_argument("res", action="store", type=int, help='Resolution of data')
  parser.add_argument("token_name", action="store", type=str, help='Token Name')
  result = parser.parse_args()

  kristina = Ingest_Data(result.path, result.res, result.token_name)

if __name__ == "__main__":
  main()
