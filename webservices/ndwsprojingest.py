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

import re
import urllib2
import json
import django
django.setup()
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from ndproj.ndprojdb import NDProjectsDB
from webservices.ndwsingest import IngestData
# from ndschema import PROJECT_SCHEMA, DATASET_SCHEMA, CHANNEL_SCHEMA
from ndlib.ndtype import READONLY_FALSE, REDIS, S3_TRUE
from nduser.models import Project
from nduser.models import Dataset
from nduser.models import Token
from nduser.models import Channel
from nduser.models import User
from webservices.ndwserror import NDWSError
from ndproj.nddataset import NDDataset
from ndproj.ndproject import NDProject
from ndproj.ndchannel import NDChannel
from ndproj.ndtoken import NDToken
import logging
logger = logging.getLogger('neurodata')

def autoIngest(webargs, post_data):
  """Create a project using a JSON file"""
  
  # setting state values for error handling
  TOKEN_CREATED = False
  PROJECT_CREATED = False
  CHANNEL_CREATED = False
  DATASET_CREATED = False
  
  nd_dict = json.loads(post_data)
  try:
    dataset_dict = nd_dict['dataset']
    project_dict = nd_dict['project']
    channels = nd_dict['channels']
    metadata_dict = nd_dict['metadata']
  except Exception, e:
    logger.error("Missing requred fields of dataset, project, channels, metadata.")
    return HttpResponseBadRequest(json.dumps("Missing required fields of dataset, project, channels, metadata. Please check if one of them is not missing."), content_type="application/json")
  
  # try:
    # DATASET_SCHEMA.validate(dataset_dict)
  # except Exception, e:
    # logger.error("Invalid Dataset schema")
    # return json.dumps("Invalid Dataset schema")
  
  # try:
    # PROJECT_SCHEMA.validate(project_dict)
  # except Exception, e:
    # logger.error("Invalid Project schema")
    # return json.dumps("Invalid Project schema")
    
  #try:
    #CHANNEL_SCHEMA.validate(channels)
  #except Exception, e:
    #print "Invalid Channel schema"
    #return json.dumps("Invalid Channel schema")

  # pr.host = 'localhost'
  # pr.s3backend = S3_TRUE
  # if pr.project_name in ['unittest','unittest2']:
    # pr.host = 'localhost'

  try:
    # Setting the user_ids to brain for now
    
    # creating ds object
    ds = NDDataset.fromJson(extractDatasetDict(dataset_dict))
    ds.user_id = 1
    
    # Checking if the posted dataset already exists
    # Setting the foreign key for dataset
    if Dataset.objects.filter(dataset_name = ds.dataset_name).exists():
      stored_ds = NDDataset.fromName(ds.dataset_name)
      if compareModelObjects(stored_ds, ds): 
        pass
        # pr.dataset_id = stored_ds.dataset_name
      else:
        logger.error("Dataset {} already exists and is different then the chosen dataset".format(ds.dataset_name))
        return HttpResponseBadRequest(json.dumps("Dataset {} already exists and is different then the chosen dataset. Please choose a different dataset name".format(ds.dataset_name)), content_type="application/json")
    else:
      ds.create()
      DATASET_CREATED = True
      # pr.dataset_id = ds.dataset_name

    # extracting project and token 
    pr, tk = extractProjectDict(project_dict)
    pr = NDProject.fromJson(ds.dataset_name, pr)
    pr.user_id = 1
    pr.kvengine = REDIS
    
    # Checking if the posted project already exists
    # Setting the foreign key for project
    if Project.objects.filter(project_name = pr.project_name).exists():
      stored_pr = NDProject.fromName(pr.project_name)
      # Checking if the existing project is same as the posted one, here we compare their datasets since python behaves wierdly with sub-objects in other objects. this is not fool-proof but works as a good hack
      tk = NDToken.fromJson(pr.project_name, tk)
      tk.user_id = 1
      if compareModelObjects(stored_pr.datasetcfg, pr.datasetcfg):
        if Token.objects.filter(token_name = tk.token_name).exists():
          stored_tk = NDToken.fromName(tk.token_name)
          # tk.project_id = stored_pr.project_name
          # Checking if the existing token is same as the posted one
          if compareModelObjects(stored_tk, tk):
            pass
          else:
            if DATASET_CREATED:
              ds.delete()
            logger.error("Token {} already exists.".format(tk.token_name))
            return HttpResponseBadRequest(json.dumps("Token {} already exists. Please choose a different token name.".format(tk.token_name)), content_type="application/json")
        else:
          # tk.project_id = stored_pr.project_name
          tk.create()
          TOKEN_CREATED = True
      else:
        if DATASET_CREATED:
          ds.delete()
        if TOKEN_CREATED:
          tk.delete()
        logger.error("Project {} already exists.".format(pr.project_name))
        return HttpResponseBadRequest(json.dumps("Project {} already exists. Please choose a different project name".format(pr.project_name)), content_type="application/json")
    else:
      try:
        pr.create()
        tk = NDToken.fromJson(pr.project_name, tk)
        tk.user_id = 1
        tk.create()
        # pd = NDProjectsDB.getProjDB(pr)
        # pd.newNDProject()
        PROJECT_CREATED = True
        TOKEN_CREATED = True
      except Exception, e:
        if TOKEN_CREATED:
          tk.delete()
        if PROJECT_CREATED:
          pr.delete()
        if DATASET_CREATED:
          ds.delete()
        logger.error("There was an error in creating the project {} database".format(pr.project_name))
        return HttpResponseBadRequest(json.dumps("There was an error in creating the project {} database".format(pr.project_name)), content_type="application/json")
      # tk.project_id = pr.project_name
      tk.create()

      TOKEN_CREATED = True
    
    ch_list = []
    for channel_name, value in channels.iteritems():
      channel_dict = channels[channel_name]
      ch, data_url, file_format, file_type = extractChannelDict(channel_dict)
      ch = NDChannel.fromJson(pr.project_name, ch)
      ch_list.append((ch, data_url, file_format, file_type))
      channel_object_list = []
    # Iterating over channel list to store channels
    for (ch, data_url, file_format, file_type) in ch_list:
      # ch.project_id = pr.project_name
      ch.user_id = 1
      # Checking if the channel already exists or not
      if not Channel.objects.filter(channel_name = ch.channel_name, project = pr.project_name).exists():
        # Maintain a list of channel objects created during this iteration and delete all even if one fails
        channel_object_list.append(ch)
        try:
          ch.create()
          # pd = NDProjectsDB.getProjDB(pr)
          # pd.newNDChannel(ch.channel_name)
          CHANNEL_CREATED = True
        except Exception, e:
          if TOKEN_CREATED:
            tk.delete()
          if CHANNEL_CREATED:
            for ch_obj in channel_object_list:
              ch_obj.delete()
          if PROJECT_CREATED:
            pr.delete()
          if DATASET_CREATED:
            ds.delete()
          logger.error("There was an error creating in the channel {} table".format(ch.channel_name))
          return HttpResponseBadRequest(json.dumps("There was an error in creating the channel {} table.".format(ch.channel_name)), content_type="application/json")
      else:
        logger.error("Channel {} already exists.".format(ch.channel_name))
        return HttpResponseBadRequest(json.dumps("Channel {} already exists. Please choose a different channel name.".format(ch.channel_name)), content_type="application/json")
      
      # checking if the posted data_url has a trialing slash or not. This becomes an issue in auto-ingest
      if data_url.endswith('/'):
        # removing the trailing slash if there exists one
        data_url = data_url[:-1]
      
      # calling celery ingest task
      from sd.tasks import ingest
      # ingest(tk.token_name, ch.channel_name, ch.resolution, data_url, file_format, file_type)
      ingest.delay(tk.token_name, ch.channel_name, ch.resolution, data_url, file_format, file_type)
      
      # calling ndworker
      # from ndworker.ndworker import NDWorker
      # worker = NDWorker(tk.token_name, ch.channel_name, ch.resolution)
      # queue_name = worker.populateQueue()
    
    # Posting to LIMS system
    # postMetadataDict(metadata_dict, pr.project_name)

  except Exception, e:
    # KL TODO Delete data from the LIMS systems
    if pr is not None and PROJECT_CREATED:
      pr.delete()
    logger.error("Error saving models. There was an error in the information posted")
    return HttpResponseBadRequest(json.dumps("FAILED. There was an error in the information you posted."), content_type="application/json")

  return HttpResponse(json.dumps("SUCCESS. The ingest process has now started."), content_type="application/json")
  # return_dict = {'queue_name' : queue_name}
  return HttpResponse(json.dumps(return_dict), content_type="application/json")

def createChannel(webargs, post_data):
  """Create a list of channels using a JSON file"""
  
  # Get the token and load the project
  try:
    m = re.match("(\w+)/createChannel/$", webargs)
    token_name = m.group(1)
  except Exception, e:
    logger.error("Error in URL format")
    raise NDWSError("Error in the URL format")
  
  nd_dict = json.loads(post_data)
  try:
    channels = nd_dict['channels']
  except Exception, e:
    logger.error("Missing channels field. Ensure that 'Channel' field exists.")
    return HttpResponseBadRequest("Missing channels field. Ensure that 'Channel' field exists.")
  
  tk = Token.objects.get(token_name=token_name)
  ur = User.objects.get(id=tk.user_id)
  pr = Project.objects.get(project_name=tk.project_id)

  ch_list = []
  for channel_name, value in channels.iteritems():
    channel_dict = channels[channel_name]
    ch_list.append(extractChannelDict(channel_dict, channel_only=True))
  
  try:
    # First iterating over the channel list to check if all the channels don't exist
    for ch in ch_list:
      if Channel.objects.filter(channel_name = ch.channel_name, project = pr.project_name).exists():
        logger.error("Channel {} already exists for project {}. Specify a different channel name".format(ch.channel_name, pr.project_name))
        return HttpResponseBadRequest("Channel {} already exists for project {}. Specify a different channel name".format(ch.channel_name, pr.project_name), content_type="text/plain")
    
    # Iterating over channel list to store channels
    for ch in ch_list:
      ch.project_id = pr.project_name
      # Setting the user_ids based on token user_id
      ch.user_id = tk.user_id
      ch.save()
      
      # Create channel database using the ndproj interface
      pd = NDProjectsDB.getProjDB(pr)
      pd.newNDChannel(ch.channel_name)
  except Exception, e:
    logger.error("Error saving models")
    # return the bad request with failed message
    return HttpResponseBadRequest("Error saving models.", content_type="text/plain")

  # return the JSON file with success
  return HttpResponse("Success. The channels were created.", content_type="text/plain")

def deleteChannel(webargs, post_data):
  """Delete a list of channels using a JSON file"""

  # Get the token and load the project
  try:
    m = re.match("(\w+)/deleteChannel/$", webargs)
    token_name = m.group(1)
  except Exception, e:
    logger.error("Error in URL format")
    raise NDWSError("Error in URL format")
  
  nd_dict = json.loads(post_data)
  try:
    channels = nd_dict['channels']
  except Exception, e:
    logger.error("Missing requred fields.")
    return HttpResponseBadRequest("Missing requred fields.")
  
  tk = Token.objects.get(token_name=token_name)
  ur = User.objects.get(id=tk.user_id)
  pr = Project.objects.get(project_name=tk.project_id)

  try:
    # Iterating over channel list to store channels
    for channel_name in channels:
      # Checking if the channel already exists or not
      if Channel.objects.get(channel_name = channel_name, project = pr.project_name):
        ch = Channel.objects.get(channel_name = channel_name, project = pr.project_name)
        # Checking if channel is readonly or not
        if ch.readonly == READONLY_FALSE:
          # delete channel table using the ndproj interface
          pd = NDProjectsDB().getProjDB(pr)
          pd.deleteNDChannel(ch.channel_name)
          ch.delete()
    return HttpResponse("Success. Channels deleted.")
  except Exception, e:
    logger.error("Error saving models. The channels were not deleted.")
    return HttpResponseBadRequest("Error saving models. The channels were not deleted.")


def postMetadataDict(metadata_dict, project_name):
  """Post metdata to the LIMS system"""

  try:
    url = 'http://{}/metadata/ocp/set/{}/'.format(settings.LIMS_SERVER, project_name)
    req = urllib2.Request(url, json.dumps(metadata_dict))
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req)
  except urllib2.URLError, e:
    logger.error("Failed URL {}".format(url))
    pass


def extractDatasetDict(ds_dict):
  """Generate a dataset object from the JSON flle"""
  
  ds = {}

  try:
    ds['dataset_name'] = ds_dict['dataset_name']
    ds['ximagesize'] = ds_dict['imagesize'][0]
    ds['yimagesize'] = ds_dict['imagesize'][1]
    ds['zimagesize'] = ds_dict['imagesize'][2]
    ds['xvoxelres'] = ds_dict['voxelres'][0]
    ds['yvoxelres'] = ds_dict['voxelres'][1]
    ds['zvoxelres'] = ds_dict['voxelres'][2]
  except Exception, e:
    logger.error("Missing required fields")
    raise NDWSError("Missing required fields")

  if 'offset' in ds_dict:
    ds['xoffset'] = ds_dict['offset'][0]
    ds['yoffset'] = ds_dict['offset'][1]
    ds['zoffset'] = ds_dict['offset'][2]
  if 'scaling' in ds_dict:
    ds['scalingoption'] = ds_dict['scaling']
  if 'scalinglevels' in ds_dict:
    ds['scalinglevels'] = ds_dict['scalinglevels']
  else:
    ds['scalinglevels'] = computeScalingLevels(imagesize)

  return json.dumps(ds)
  
def computeScalingLevels(imagesize):
  """Dynamically decide the scaling levels"""

  ximagesz, yimagesz, zimagesz = imagesize
  scalinglevels = 0
  # When both x and y dimensions are below 1000 or one is below 100 then stop
  while (ximagesz>1000 or yimagesz>1000) and ximagesz>500 and yimagesz>500:
    ximagesz = ximagesz / 2
    yimagesz = yimagesz / 2
    scalinglevels += 1

  return scalinglevels

def extractProjectDict(pr_dict):
  """Generate a project object from the JSON flle"""

  pr = {}
  tk = {}

  try:
    pr['project_name'] = pr_dict['project_name']
  except Exception, e:
    logger.error("Missing required fields")
    raise NDWSError("Missing required fields")

  if 'token_name' in pr_dict:
    tk['token_name'] = pr_dict['token_name']
  else:
    tk['token_name'] = pr_dict['project_name']
  if 'public' in pr_dict:
    tk['public'] = pr_dict['public']
  return json.dumps(pr), json.dumps(tk)

def extractChannelDict(ch_dict, channel_only=False):
  """Generate a channel object from the JSON flle"""

  ch = {}
  try:
    ch['channel_name'] = ch_dict['channel_name']
    ch['channel_datatype'] =  ch_dict['datatype']
    ch['channel_type'] = ch_dict['channel_type']
    if 'timerange' in ch_dict:
      ch['starttime'] = ch_dict['timerange'][0]
      ch['endtime'] = ch_dict['timerange'][1]
    if not channel_only:
      data_url = ch_dict['data_url']
      file_format = ch_dict['file_format']
      file_type = ch_dict['file_type']
  except Exception, e:
    logger.error("Missing required fields")
    raise NDWSError("Missing required fields")
    
  if 'exceptions' in ch_dict:
    ch['exceptions'] = ch_dict['exceptions']
  if 'resolution' in ch_dict:
    ch['resolution'] = ch_dict['resolution']
  if 'windowrange' in ch_dict:
    ch['startwindow'] = ch_dict['windowrange'][0]
    ch['endwindow'] = ch_dict['windowrange'][1]
  if 'readonly' in ch_dict:
    ch['readonly'] = ch_dict['readonly']

  if not channel_only:
    return (json.dumps(ch), data_url, file_format, file_type)
  else:
    return ch

def createJson(dataset, project, channel_list, metadata={}, channel_only=False):
  """Genarate ND json object"""
  
  nd_dict = {}
  nd_dict['channels'] = {}
  if not channel_only:
    nd_dict['dataset'] = createDatasetDict(*dataset)
    nd_dict['project'] = createProjectDict(*project)
    nd_dict['metadata'] = metadata
  
  for channel_name, value in channel_list.iteritems():
    value = value + (channel_only,)
    nd_dict['channels'][channel_name] = createChannelDict(*value)
  
  return json.dumps(nd_dict, sort_keys=True, indent=4)

# def createDatasetDict(dataset_name, imagesize, voxelres, offset=[0,0,0], timerange=[0,0], scalinglevels=0, scaling=0):
  # """Generate the dataset dictionary"""

def postMetadataDict(metadata_dict, project_name):
  """Post metdata to the LIMS system"""

  try:
    url = 'http://{}/lims/{}/'.format(settings.LIMS_SERVER, project_name)
    req = urllib2.Request(url, json.dumps(metadata_dict))
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req)
  except urllib2.URLError, e:
    logger.error("Failed URL {}".format(url))
    pass


# def extractDatasetDict(ds_dict):
  # """Generate a dataset object from the JSON flle"""

  # ds = Dataset();
  
  # try:
    # ds.dataset_name = ds_dict['dataset_name']
    # imagesize = [ds.ximagesize, ds.yimagesize, ds.zimagesize] = ds_dict['imagesize']
    # [ds.xvoxelres, ds.yvoxelres, ds.zvoxelres] = ds_dict['voxelres']
  # except Exception, e:
    # logger.error("Missing required fields")
    # raise NDWSError("Missing required fields")

  # if 'offset' in ds_dict:
    # [ds.xoffset, ds.yoffset, ds.zoffset] = ds_dict['offset']
  # if 'scaling' in ds_dict:
    # ds.scalingoption = ds_dict['scaling']
  # if 'scalinglevels' in ds_dict:
    # ds.scalinglevels = ds_dict['scalinglevels']
  # else:
    # ds.scalinglevels = computeScalingLevels(imagesize)

  # return ds
  
def computeScalingLevels(imagesize):
  """Dynamically decide the scaling levels"""

  ximagesz, yimagesz, zimagesz = imagesize
  scalinglevels = 0
  # When both x and y dimensions are below 1000 or one is below 100 then stop
  while (ximagesz>1000 or yimagesz>1000) and ximagesz>500 and yimagesz>500:
    ximagesz = ximagesz / 2
    yimagesz = yimagesz / 2
    scalinglevels += 1

  return scalinglevels

def createJson(dataset, project, channel_list, metadata={}, channel_only=False):
  """Genarate ND json object"""
  
  nd_dict = {}
  nd_dict['channels'] = {}
  if not channel_only:
    nd_dict['dataset'] = createDatasetDict(*dataset)
    nd_dict['project'] = createProjectDict(*project)
    nd_dict['metadata'] = metadata
  
  for channel_name, value in channel_list.iteritems():
    nd_dict['channels'][channel_name] = createChannelDict(*value)
  
  return json.dumps(nd_dict, sort_keys=True, indent=4)

def createDatasetDict(dataset_name, imagesize, voxelres, offset=[0,0,0], scalinglevels=0, scaling=0):
  """Generate the dataset dictionary"""

  # dataset format = (dataset_name, [ximagesz, yimagesz, zimagesz], [[xvoxel, yvoxel, zvoxel], [xoffset, yoffset, zoffset], scalinglevels, scaling)
  
  dataset_dict = {}
  dataset_dict['dataset_name'] = dataset_name
  dataset_dict['imagesize'] = imagesize
  dataset_dict['voxelres'] = voxelres
  if offset is not None:
    dataset_dict['offset'] = offset
  if scalinglevels is not None:
    dataset_dict['scalinglevels'] = scalinglevels
  if scaling is not None:
    dataset_dict['scaling'] = scaling
  return dataset_dict

def createChannelDict(channel_name, datatype, channel_type, data_url, file_format, file_type, time_range=[0,0], exceptions=0, resolution=0, windowrange=[0,0], readonly=0, channel_only=False):
  """Genearte the project dictionary"""
  
  # channel format = (channel_name, datatype, channel_type, data_url, file_type, file_format, exceptions, resolution, timerange, windowrange, readonly)
  
  channel_dict = {}
  channel_dict['channel_name'] = channel_name
  channel_dict['datatype'] = datatype
  channel_dict['channel_type'] = channel_type
  if exceptions is not None:
    channel_dict['exceptions'] = exceptions
  if resolution is not None:
    channel_dict['resolution'] = resolution
  if timerange is not None:
    channel_dict['timerange'] = timerange
  if windowrange is not None:
    channel_dict['windowrange'] = windowrange
  if readonly is not None:
    channel_dict['readonly'] = readonly
  if not channel_only:
    channel_dict['data_url'] = data_url
    channel_dict['file_format'] = file_format
    channel_dict['file_type'] = file_type
  return channel_dict

def createProjectDict(project_name, token_name='', public=0):
  """Genarate the project dictionary"""
  
  # project format = (project_name, token_name, public)
  
  project_dict = {}
  project_dict['project_name'] = project_name
  if token_name is not None:
    project_dict['token_name'] = project_name if token_name == '' else token_name
  if public is not None:
    project_dict['public'] = public
  return project_dict


def compareModelObjects(obj1, obj2, excluded_keys=['_state']):
  """Compare two model objects"""

  for key, value in obj1.__dict__.items():
    if key in excluded_keys:
      continue
    if obj2.__dict__[key] == value:
      pass
    else:
      return False
  return True
