import geemap as gee

import ee
from ee import batch
# import geemap as gee
import os
import requests
from time import time
from multiprocessing.pool import ThreadPool
import io
from contextlib import redirect_stdout
import json




# ee.Authenticate()
ee.Initialize()

class Downloader():

  def __init__(self):
    self.collection = ee.ImageCollection('COPERNICUS/S1_GRD')
    self.geojson_path = "/Users/michaelcruickshank/Downloads/Yelnya_Base.geojson"
    self.start_date = "2021-10-01"
    self.end_date = "2022-01-20"
    self.region = None 
    self.image_ids = []
    self.url_dict = {}

  def run(self):
    self.get_bands(self.collection)
    self.filterbygeometry(self.collection, self.geojson_path)
    self.filterbydaterange(self.collection, self.start_date, self.end_date)
    self.get_region(self.geojson_path)
    # self.get_final_inputs(self.collection, self.geojson_path, self.start_date, self.end_date)
    self.get_image_ids(self.collection)
    self.get_download_urls(self.collection, self.image_ids)
    # self.run_url_reponses(self.url_dict)
    self.get_metadata_jsons(self.collection, self.image_ids)


  def band_adder(self, image):
    vh_vv = image.select("VH").subtract(image.select("VV")).rename("VH-VV")
    return image.addBands(vh_vv)

  def get_bands(self, collection):
    collection_both = self.collection.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).filter(ee.Filter.eq('instrumentMode', 'IW'))
    col_final = collection_both.map(self.band_adder) 
    col_final_no_angle = col_final.map(lambda image: image.select(['VV', 'VH', 'VH-VV']))
    self.collection = col_final_no_angle

  #filters an image collection by a single geometry in geojson format
  def filterbygeometry(self, collection, geojson_path):
    geometry = gee.geojson_to_ee(self.geojson_path)
    geom_filtered_col = self.collection.filterBounds(geometry)
    self.collection = geom_filtered_col #returns image collection

  #filters an image collection by a range of dates in yyyy-mm-dd format
  def filterbydaterange(self, collection, start_date, end_date):
    date_filtered_col = self.collection.filterDate(self.start_date, self.end_date)
    self.collection = date_filtered_col #returns image collection

  def get_region(self, geojson_path):
    geometry = gee.geojson_to_ee(self.geojson_path)
    poi = geometry.geometry().centroid(maxError = 1)
    aoi = poi.buffer(3000)
    aoi = aoi.bounds()
    self.region = aoi

  def getCover(self, image, aoi, scale):
    totPixels = ee.Number(image.unmask(1).reduceRegion(reducer = ee.Reducer.count(), scale = scale, geometry = aoi).values().get(0))
    actPixels = ee.Number(image.reduceRegion(reducer = ee.Reducer.count(), scale = scale, geometry = aoi).values().get(0))
    percCover = actPixels.divide(totPixels).multiply(100).round()
    return image.set('percCover', percCover)


  def filter_incompletes(self, collection, region):
    coll_with_zero_flag = self.collection.map(lambda image: self.getCover(image, self.region, 10))
    filtered_collection = coll_with_zero_flag.filterMetadata('percCover', 'equals', 100)
    self.collection = filtered_collection

  # def get_final_inputs(self, collection, geojson_path, start_date, end_date):
  #   self.collection = self.get_bands(self.collection)
  #   self.collection = self.filterbygeometry(self.collection, self.geojson_path)
  #   self.collection = self.filterbydaterange(self.collection, self.start_date, self.end_date)
  #   self.region = self.get_region(self.geojson_path)
  #   self.collection = self.filter_incompletes(self.collection, self.region)

  def get_image_ids(self, collection):
    self.image_ids = self.collection.aggregate_array("system:id").getInfo()

  def is_finished_downloading(task):
    if task.status()["state"] == "COMPLETED":
      return True
    else:
      return False

  def get_download_urls(self, collection, image_ids):
    visParams = {
    'bands': ['VV', 'VH', 'VH-VV'],
    'min': -5,
    'max': -20,
    'dimensions': 500,
    'framesPerSecond': 2,
    'region': self.region,
    'crs': "EPSG:32637"}
    for image_id in self.image_ids:
      split_name = image_id.split("/")
      filename = split_name[-1]
      image = self.collection.filter(ee.Filter.eq("system:id", image_id)).first()
      self.url_dict[image_id] = image.getDownloadUrl(visParams)
      print(image_id)
      image.getDownloadUrl(visParams)

  def url_response(self, url, file_name):
    response = requests.get(url, stream = True)
    if response.status_code == 200:
      with open(file_name, 'wb') as f:
        for chunk in response.iter_content(chunk_size=128):
          f.write(chunk)

  def run_url_reponses(self, url_dict):
    for key in self.url_dict:
      url = url_dict[key]
      split_name = key.split("/")
      print(split_name[-1])
      file_name = split_name[-1] + ".zip"
      print("file_name: " + file_name)
      print("url " + url)
      self.url_response(url, file_name)

  def get_metadata_jsons(self, collection, image_ids):
    for image_id in self.image_ids:
      image = self.collection.filter(ee.Filter.eq("system:id", image_id)).first()
      f = io.StringIO()
      data = image.getInfo()
      split_name = image_id.split("/")
      filename = split_name[-1]
      outdir = "/Users/michaelcruickshank/Documents/SARveillance/app/metadata/"
      outpath = outdir+filename+".json"
      with open(outpath, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)





if __name__ == '__main__':
  dwnld = Downloader()
  dwnld.run()

# class TaskObserver():
#   def __init__(self, task):
#     self.task = task

#   @property
#   def status(self):
#     return self._task.status['state']

#   @status.setter
#   def status(self, new_status):
#     self._status = new_status
#     self.status_changed()

#   def status_changed(self):
#     print("status changed: ")
#     print(self.status)

# def is_finished_downloading(task):
#   if task.status()["state"] == "COMPLETED":
#     return True
#   else:
#     return False
