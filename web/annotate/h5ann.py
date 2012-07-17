import numpy as np

import urllib2
import tempfile
import h5py
import csv
import cStringIO
import collections

import sys

import empaths
import annotation
import anndb
import annproj
import dbconfig

from pprint import pprint

#
#  class to define the HDF5 format of annotations.
#

# TODO implement data and author
#  support missing values
# suport untyped files

"""The HDF5 format currently looks like:

/  (Root) group:

ANNOTATION_TYPE (int)
ANNOTATION_ID (int)
RESOLUTION (int optional) defaults to project resolution
XYZOFFSET ( int[3] optional defined with volume )
CUTOUT ( int32 3-d array optional defined with XYZOFFSET )
VOXELS ( int32[][3] optional if defined XYZOFFSET and CUTOUT must be empty ) 

METADATA group;

 # metadata for all annotations
 CONFIDENCE (float)
 STATUS (int) 
 KVPAIRS   (string containing csv pairs)
 AUTHOR ( string ) 

 # for seeds

 PARENT (int)
 POSITION (int[3])
 CUBE_LOCATION (int)
 SOURCE (int)

 # for segments:

 SEGMENTCLASS (int)
 PARENTSEED (int)
 SYNAPSES (int[]) 
 ORGANELLES ( int[])

 # for synapses:

 SYNAPSE_TYPE (int)
 WEIGHT (float)
 SEEDS (int[]) 
 SEGMENTS ( int[ ][2] )

 # for neurons
 SEGMENTS ( int[] )

 # for organelles
 ORGANELLECLASS (int)
 PARENTSEED (int)
 SEEDS (int[]) 

"""


class H5Annotation:
  """Class to move data into and out of HDF5 files"""

  def __init__( self, annotype, annoid ):
    """Create an HDF5 file and simple structure
      calls with data as a list of voxels and location == None for voxel lists
      call with data as an array of data and xyzoffset for a volume
     """

    # Create an in-memory HDF5 file
    self.tmpfile = tempfile.NamedTemporaryFile()
    self.h5fh = h5py.File ( self.tmpfile.name )

    # Annotation type
    self.h5fh.create_dataset ( "ANNOTATION_TYPE", (1,), np.uint32, data=annotype )
    self.h5fh.create_dataset ( "ANNOTATION_ID", (1,), np.uint32, data=annoid )
    
    # Create a metadata group
    self.mdgrp = self.h5fh.create_group ( "METADATA" ) 

  def __del__ ( self ):
    """Destructor"""
    self.h5fh.close()

  def fileReader( self ):
    """Return a file read stream to be transferred as put data"""
    self.h5fh.flush()
    self.tmpfile.seek(0)
    return self.tmpfile.read()

  def addVoxels ( self, voxlist ):
    """Add the list of voxels to the HDF5 file"""
    self.h5fh.create_dataset ( "VOXELS", (len(voxlist),3), np.uint32, data=voxlist )     

  def addCutout ( self, corner, volume ):
    """Add the cutout  to the HDF5 file"""
    self.h5fh.create_dataset ( "XYZOFFSET", (3,), np.uint32, data=corner )     
    self.h5fh.create_dataset ( "CUTOUT", volume.shape, np.uint32, data=volume )     

############## Converting HDF5 to Annotations

def H5toAnnotation ( h5fh ):
  """Return an annotation constructed from the contents of this HDF5 file"""

  # get the annotation type
  if h5fh.get('ANNOTATION_TYPE'):
    annotype = h5fh['ANNOTATION_TYPE'][0]
  else:
    annotype = annotation.ANNO_ANNOTATION

  # And get the metadata group
  mdgrp = h5fh.get('METADATA')

  if annotype == annotation.ANNO_SEED:

    # Create the appropriate annotation type
    anno = annotation.AnnSeed()

    # Load metadata if it exists
    if mdgrp:
      # load the seed specific metadata
      if mdgrp.get('PARENT'):
        anno.parent = mdgrp['PARENT'][0]
      if mdgrp.get('POSITION'):
        anno.position = mdgrp['POSITION'][:]
      if mdgrp.get('CUBE_LOCATION'):
        anno.cubelocation = mdgrp['CUBE_LOCATION'][0]
      if mdgrp.get('SOURCE'):
        anno.source = mdgrp['SOURCE'][0] 

  elif annotype == annotation.ANNO_SYNAPSE:
    
    # Create the appropriate annotation type
    anno = annotation.AnnSynapse()

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('SYNAPSE_TYPE'):
        anno.synapse_type = mdgrp['SYNAPSE_TYPE'][0]
      if mdgrp.get('WEIGHT'):
        anno.weight = mdgrp['WEIGHT'][0]
      if mdgrp.get('SEEDS') and len(mdgrp['SEEDS'])!=0:
        anno.seeds = mdgrp['SEEDS'][:]
      if mdgrp.get('SEGMENTS') and len(mdgrp['SEGMENTS'])!=0:
        anno.segments = mdgrp['SEGMENTS'] [:]

  elif annotype == annotation.ANNO_SEGMENT:
    
    # Create the appropriate annotation type
    anno = annotation.AnnSegment()

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('PARENTSEED'):
        anno.parentseed = mdgrp['PARENTSEED'][0]
      if mdgrp.get('SEGMENTCLASS'):
        anno.segmentclass = mdgrp['SEGMENTCLASS'][0]
      if mdgrp.get('SYNAPSES') and len(mdgrp['SYNAPSES'])!=0:
        anno.synapses = mdgrp['SYNAPSES'][:]
      if mdgrp.get('ORGANELLES') and len(mdgrp['ORGANELLES'])!=0:
        anno.organelles = mdgrp['ORGANELLES'][:]

  elif annotype == annotation.ANNO_NEURON:
    
    # Create the appropriate annotation type
    anno = annotation.AnnNeuron()

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('SEGMENTS') and len(mdgrp['SEGMENTS'])!=0:
        anno.segments = mdgrp['SEGMENTS'][:]

  elif annotype == annotation.ANNO_ORGANELLE:
    
    # Create the appropriate annotation type
    anno = annotation.AnnOrganelle()

    # Load metadata if it exists
    if mdgrp:
      # load the synapse specific metadata
      if mdgrp.get('PARENTSEED'):
        anno.parentseed = mdgrp['PARENTSEED'][0]
      if mdgrp.get('ORGANELLECLASS'):
        anno.organelleclass = mdgrp['ORGANELLECLASS'][0]
      if mdgrp.get('SEEDS') and len(mdgrp['SEEDS'])!=0:
        anno.seeds = mdgrp['SEEDS'][:]
      if mdgrp.get('CENTROID'):
        anno.centroid = mdgrp['CENTROID'][:]

  # No special action if it's a no type
  elif annotype == annotation.ANNO_ANNOTATION:
    # Just create a generic annotation object
    anno = annotation.Annotation()

  else:
    raise Exception ("Dont support this annotation type yet")

  # now load the annotation common fields
  if h5fh.get('ANNOTATION_ID'):
    anno.annid = h5fh['ANNOTATION_ID'][0]

  if mdgrp:
    # now load the metadata common fields
    if mdgrp.get('STATUS'):
      anno.status = mdgrp['STATUS'][0]
    if mdgrp.get('CONFIDENCE'):
      anno.confidence = mdgrp['CONFIDENCE'][0]
    if mdgrp.get('AUTHOR'):
      anno.author = mdgrp['AUTHOR'][0]

    # and the key/value pairs
    if mdgrp.get('KVPAIRS'):
      fstring = cStringIO.StringIO( mdgrp['KVPAIRS'][0] )
      csvr = csv.reader(fstring, delimiter=',')
      for r in csvr:
        anno.kvpairs[r[0]] = r[1] 

  return anno

def H5GetVoxels ( h5fh ):
  """Return the voxel data associated with the annotation"""

  if h5fh.get('VOXELS'):
    return h5fh['VOXELS']
  else:
    return None

def H5GetVolume ( h5fh ):
  """Return the volume associated with the annotation"""

  if h5fh.get('XYZOFFSET'):
    if h5fh.get('CUTOUT'):
      return (h5fh['XYZOFFSET'], h5fh['CUTOUe'])
    else:
      # TODO log message improper data format
      pass
  else:
    return None

############## Converting Annotation to HDF5 ####################

def BasetoH5 ( anno, annotype ):
  """Convert an annotation to HDF5 for interchange"""

  h5anno = H5Annotation ( annotype, anno.annid )

  # Set Annotation specific metadata
  h5anno.mdgrp.create_dataset ( "STATUS", (1,), np.uint32, data=anno.status )
  h5anno.mdgrp.create_dataset ( "CONFIDENCE", (1,), np.float, data=anno.confidence )
  h5anno.mdgrp.create_dataset ( "AUTHOR", (1,), dtype=h5py.special_dtype(vlen=str), data=anno.author )

  # Turn our dictionary into a csv file
  fstring = cStringIO.StringIO()
  csvw = csv.writer(fstring, delimiter=',')
  csvw.writerows([r for r in anno.kvpairs.iteritems()]) 

  # User-defined metadata
  h5anno.mdgrp.create_dataset ( "KVPAIRS", (1,), dtype=h5py.special_dtype(vlen=str), data=fstring.getvalue())

  return h5anno


def SynapsetoH5 ( synapse ):
  """Convert a synapse to HDF5"""

  # First create the base object
  h5synapse = BasetoH5 ( synapse, annotation.ANNO_SYNAPSE )

  # Then customize
  h5synapse.mdgrp.create_dataset ( "WEIGHT", (1,), np.float, data=synapse.weight )
  h5synapse.mdgrp.create_dataset ( "SYNAPSE_TYPE", (1,), np.uint32, data=synapse.synapse_type )

  # Lists (as arrays)
  if ( synapse.seeds != [] ):
    h5synapse.mdgrp.create_dataset ( "SEEDS", (len(synapse.seeds),), np.uint32, synapse.seeds )
  else:
    h5synapse.mdgrp.create_dataset ( "SEEDS", (0,), np.uint32 )

  #  segments and segment type
  if ( synapse.segments != [] ):
    h5synapse.mdgrp.create_dataset ( "SEGMENTS", (len(synapse.segments),2), np.uint32, data=synapse.segments)
  else:
    h5synapse.mdgrp.create_dataset ( "SEGMENTS", (0,0), np.uint32 )

  return h5synapse


def SeedtoH5 ( seed ):
  """Convert a seed to HDF5"""

  # First create the base object
  h5seed = BasetoH5 ( seed, annotation.ANNO_SEED )

  # convert these  to enumerations??
  h5seed.mdgrp.create_dataset ( "PARENT", (1,), np.uint32, data=seed.parent )
  h5seed.mdgrp.create_dataset ( "CUBE_LOCATION", (1,), np.uint32, data=seed.cubelocation )
  h5seed.mdgrp.create_dataset ( "SOURCE", (1,), np.uint32, data=seed.source )     
  if seed.position != [None, None, None]:
    h5seed.mdgrp.create_dataset ( "POSITION", (3,), np.uint32, data=seed.position )     

  return h5seed


def SegmenttoH5 ( segment ):
  """Convert a segment to HDF5"""

  # First create the base object
  h5segment = BasetoH5 ( segment, annotation.ANNO_SEGMENT )

  # Then customize
  h5segment.mdgrp.create_dataset ( "SEGMENTCLASS", (1,), np.float, data=segment.segmentclass )
  h5segment.mdgrp.create_dataset ( "PARENTSEED", (1,), np.uint32, data=segment.parentseed )

  # Lists (as arrays)
  if ( segment.synapses != [] ):
    h5segment.mdgrp.create_dataset ( "SYNAPSES", (len(segment.synapses),), np.uint32, segment.synapses )
  else:
    h5segment.mdgrp.create_dataset ( "SYNAPSES", (0,), np.uint32 )

  if ( segment.organelles != [] ):
    h5segment.mdgrp.create_dataset ( "ORGANELLES", (len(segment.organelles),), np.uint32, segment.organelles )
  else:
    h5segment.mdgrp.create_dataset ( "ORGANELLES", (0,), np.uint32 )

  return h5segment


def NeurontoH5 ( neuron ):
  """Convert a neuron to HDF5"""

  # First create the base object
  h5neuron = BasetoH5 ( neuron, annotation.ANNO_NEURON )

  # Lists (as arrays)
  if ( neuron.segments != [] ):
    h5neuron.mdgrp.create_dataset ( "SEGMENTS", (len(neuron.segments),), np.uint32, neuron.segments )
  else:
    h5neuron.mdgrp.create_dataset ( "SEGMENTS", (0,), np.uint32 )

  return h5neuron


def OrganelletoH5 ( organelle ):
  """Convert a organelle to HDF5"""

  # First create the base object
  h5organelle = BasetoH5 ( organelle, annotation.ANNO_ORGANELLE )

  # Then customize
  h5organelle.mdgrp.create_dataset ( "ORGANELLECLASS", (1,), np.uint32, data=organelle.organelleclass )
  h5organelle.mdgrp.create_dataset ( "PARENTSEED", (1,), np.uint32, data=organelle.parentseed )

  # Lists (as arrays)
  if ( organelle.seeds != [] ):
    h5organelle.mdgrp.create_dataset ( "SEEDS", (len(organelle.seeds),), np.uint32, organelle.seeds )
  else:
    h5organelle.mdgrp.create_dataset ( "SEEDS", (0,), np.uint32 )
    
  if organelle.centroid != [None, None, None]:
    h5organelle.mdgrp.create_dataset ( "CENTROID", (3,), np.uint32, data=organelle.centroid )     

  return h5organelle


def AnnotationtoH5 ( anno ):
  """Operate polymorphically on annotations"""

  if anno.__class__ == annotation.AnnSynapse:
    return SynapsetoH5 ( anno )
  elif anno.__class__ == annotation.AnnSeed:
    return SeedtoH5 ( anno )
  if anno.__class__ == annotation.AnnSegment:
    return SegmenttoH5 ( anno )
  if anno.__class__ == annotation.AnnNeuron:
    return NeurontoH5 ( anno )
  if anno.__class__ == annotation.AnnOrganelle:
    return OrganelletoH5 ( anno )
  elif anno.__class__ == annotation.Annotation:
    return BasetoH5 ( anno, annotation.ANNO_ANNOTATION )
  else:
    raise Exception ("(AnnotationtoH5) Does not support this annotation type yet")


def PackageIDs ( annoids ):
  """Create an HDF5 file that contains a list of IDs in a field entitled ANNOIDS
      and return a file reader for that HDF5 file"""

  # Create an in-memory HDF5 file
  tmpfile = tempfile.NamedTemporaryFile()
  h5fh = h5py.File ( tmpfile.name )

  h5fh.create_dataset ( "ANNOIDS", annoids.shape, np.uint32, data=annoids )     

  h5fh.flush()
  tmpfile.seek(0)
  return tmpfile.read()


