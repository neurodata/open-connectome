#!/bin/bash

File="h5post.py"
host="localhost"
project="kat11_syn"
path="/home/priya/kat11hdf5/anno"


for i in {4277..6075}
do
	echo python $File $host $project $path$i.h5
	
	python $File $host $project $path$i.h5
done	
