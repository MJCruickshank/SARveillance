#!/bin/bash

#########################################
# Installing python packages needed
# using pip and conda. Both pip and 
# conda need to be installed before.
#########################################

conda install proj==7.2.0
pip install pyproj==3.2.1
pip install geemap==0.11.0
conda install -c conda-forge cartopy
pip install pandas==1.3.5