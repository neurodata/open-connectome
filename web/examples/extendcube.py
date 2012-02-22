import argparse
import empaths
import dbconfig
import dbconfighayworth5nm
import numpy as np
import urllib, urllib2
import cStringIO
import sys

import anncube
import anndb
import zindex

def main():

  parser = argparse.ArgumentParser(description='Cutout a portion of the database.')
  parser.add_argument('entity', action="store", type=int )
  parser.add_argument('xlow', action="store", type=int )
  parser.add_argument('xhigh', action="store", type=int)
  parser.add_argument('ylow', action="store", type=int)
  parser.add_argument('yhigh', action="store", type=int)
  parser.add_argument('zlow', action="store", type=int)
  parser.add_argument('zhigh', action="store", type=int)

  result = parser.parse_args()


  voxlist= []

  for k in range (result.zlow,result.zhigh):
    for j in range (result.ylow,result.yhigh):
      for i in range (result.xlow,result.xhigh):
        voxlist.append ( [ i,j,k ] )

  WS = True
  # Use the Web services
  if ( WS == True ): 


    url = "http://0.0.0.0:8080/hayworth5nm.annotate/npextend/%s/overwrite/" \
             % result.entity

    print url

    # Encode the voxelist an pickle
    fileobj = cStringIO.StringIO ()
    np.save ( fileobj, voxlist )

    # Build the post request
    req = urllib2.Request(url, fileobj.getvalue())
    response = urllib2.urlopen(req)
    the_page = response.read()

    print the_page

  # Insert via object
  else: 
    dbcfg = dbconfighayworth5nm.dbConfigHayworth5nm()

    annoDB = anndb.AnnotateDB ( dbcfg )
    # Build a grayscale file and display
    annoDB.extendEntity ( result.id, voxlist, 'O'  )

    print "Extended entity with identifier = ", result.id


if __name__ == "__main__":
      main()




