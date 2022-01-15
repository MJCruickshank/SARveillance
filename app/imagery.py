import os
import ee
import glob
from geemap import cartoee
from imagery_utils import new_get_image_collection_gif

class Imagery():

  north_arrow_dict1 = {
      "text": "N",
      "xy": (0.1, 0.3),
      "arrow_length": 0.15,
      "text_color": "white",
      "arrow_color": "white",
      "fontsize": 20,
      "width": 5,
      "headwidth": 15,
      "ha": "center",
      "va": "center"
      }

  def __init__(self):
    cartoee.get_image_collection_gif = new_get_image_collection_gif
    self.poi = None    

  def set_poi(self, poi, outpath):
    self.poi = poi
    base_path = os.path.join(outpath, 'BaseTimeseries', self.poi['name'])
    if not os.path.exists(base_path):
      os.makedirs(base_path) 
    self.outpath = base_path

  def get_collection(self):
    collection = ee.ImageCollection('COPERNICUS/S1_GRD')
    collection_both = collection.filter(ee.Filter.listContains(
        'transmitterReceiverPolarisation', 'VV')).filter(ee.Filter.eq('instrumentMode', 'IW'))
    self.col_final = collection_both.map(self.band_adder)

  def band_adder(self, image):
    vh_vv = image.select("VH").subtract(image.select("VH")).rename("VH-VV")
    return image.addBands(vh_vv)

  def generate_base_aoi(self):
    latitude = self.poi['lat']
    longitude = self.poi['lon']
    base_point = ee.Geometry.Point([float(longitude), float(latitude)])
    base_buffer = base_point.buffer(3000)
    return base_buffer.bounds()

  def get_filtered_col(self, col, base_name):
    base_aoi = self.generate_base_aoi()
    filtered_col = col.filterBounds(base_aoi)
    clipped_col = filtered_col.map(lambda image: image.clip(base_aoi))
    return clipped_col

  def cleanup_poi_data(self):
    files = glob.glob(f'{self.outpath}/*')
    for f in files:
      os.remove(f)

  def generate_timeseries_gif(self, max_frames):

    # cleanup
    self.cleanup_poi_data()
    
    # filter
    col_final_recent = self.col_final.filterDate(self.poi['start_date'], self.poi['end_date']) 
    col_filtered = self.get_filtered_col(col_final_recent, self.poi['name']).sort("system:time_start")
    
    # base aoi
    aoi = self.generate_base_aoi()
    minmax = col_filtered.first().reduceRegion(ee.Reducer.minMax(), aoi)
    max = minmax.getNumber("VV_max").getInfo()
    min = minmax.getNumber("VV_min").getInfo()
    w = 0.4
    h = 0.4
    region = [self.poi['lon']+w, self.poi['lat']-h, self.poi['lon']-w, self.poi['lat']+h]
    
    # out file stuff
    filename = self.poi['name']+".gif"
    out_gif = os.path.join(self.outpath, filename)
    
    # some gif params
    visParams = {
    'bands': ['VV', 'VH', 'VH-VV'],
    'min': min,
    'max': max,
    'dimensions': 500,
    'framesPerSecond': 2,
    'region': aoi,
    'crs': "EPSG:4326"}

    # get all images and create gif
    return cartoee.get_image_collection_gif(
      ee_ic = col_filtered,
      out_dir = self.outpath,
      out_gif = self.poi['name'] + ".gif",
      vis_params = visParams,
      region = region,
      fps = 2,
      mp4 = False,
      grid_interval = (0.2, 0.2),
      plot_title = self.poi['name'],
      date_format = 'YYYY-MM-dd',
      fig_size = (10, 10),
      dpi_plot = 100,
      file_format = "png",
      north_arrow_dict = self.north_arrow_dict1,
      verbose = True,
      max_frames = max_frames
    )