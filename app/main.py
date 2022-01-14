import os
import sys
import ee
import sys
import geemap as gee
from geemap import cartoee
import pandas as pd
from imagery_utils import new_get_image_collection_gif

base_name = sys.argv[1]
start_date= sys.argv[2]
end_date = sys.argv[3] 
outpath = sys.argv[4]

class SAREXPLORER():
  scale_bar_dict1 = {
      "length": 1, 
      "xy": (0.1, 0.05), 
      "linewidth": 3,
      "fontsize": 20,
      "color": "black",
      "unit": "km",
      "ha": "center",
      "va": "bottom"
      }

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
    self.gee = gee
    self.bases = []
    self.col_final = None
    self.dirname = os.path.dirname(__file__)
    self.outpath = self.dirname+"/Data/"


  def run(self):
    self.auth()
    self.get_bases()
    self.get_collection()
    self.create_imagery()

  def auth(self):
    #self.gee.ee.Authenticate()
    self.gee.ee_initialize()

  def get_bases(self):
    self.bases = pd.read_csv("bases_df.csv")

  def get_collection(self):
    collection = ee.ImageCollection('COPERNICUS/S1_GRD')
    collection_both = collection.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).filter(ee.Filter.eq('instrumentMode', 'IW'))
    composite_col = collection_both.map(lambda image: image.select("VH").subtract(image.select("VH")).rename("VH-VV"))
    self.col_final = collection_both.map(self.band_adder)

  def band_adder(self, image):
    vh_vv = image.select("VH").subtract(image.select("VH")).rename("VH-VV")
    return image.addBands(vh_vv)

  def generate_base_aoi(self, base_name):
    base_gdf = self.bases.loc[self.bases.Name == base_name]
    latitude = base_gdf.iloc[0]["lat"]
    longitude = base_gdf.iloc[0]["lon"]
    base_point = ee.Geometry.Point([float(longitude), float(latitude)])
    base_buffer = base_point.buffer(3000)
    base_bounds = base_buffer.bounds()
    return base_bounds

  def get_filtered_col(self, col, base_name):
    base_aoi = self.generate_base_aoi(base_name)
    filtered_col = col.filterBounds(base_aoi)
    clipped_col = filtered_col.map(lambda image: image.clip(base_aoi))
    return clipped_col

  def generate_timeseries_gif(self, base_name, start_date, end_date, outpath):
    col_final_recent = self.col_final.filterDate(start_date, end_date) #.sort("system:time_start")
    col_filtered = self.get_filtered_col(col_final_recent, base_name).sort("system:time_start")
    aoi = self.generate_base_aoi(base_name)
    minmax = col_filtered.first().reduceRegion(ee.Reducer.minMax(), aoi)
    max = minmax.getNumber("VV_max").getInfo()
    min = minmax.getNumber("VV_min").getInfo()
    base_gdf = self.bases.loc[self.bases.Name == base_name]
    lat = base_gdf.iloc[0]["lat"]
    lon = base_gdf.iloc[0]["lon"]
    w = 0.4
    h = 0.4
    region = [lon+w, lat-h, lon-w, lat+h]
    out_dir = os.path.expanduser(outpath)
    filename = base_name+".gif"
    out_gif = os.path.join(out_dir, filename)
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    visParams = {
    'bands': ['VV', 'VH', 'VH-VV'],
    'min': min,
    'max': max,
    'dimensions': 500,
    'framesPerSecond': 2,
    'region': aoi,
    'crs': "EPSG:32637"}
    return cartoee.get_image_collection_gif(
      ee_ic = col_filtered, #.sort("system:time_start"),
      out_dir = os.path.expanduser(outpath+"BaseTimeseries/"+base_name+"/"),
      out_gif = base_name + ".gif",
      vis_params = visParams,
      region = region,
      fps = 2,
      mp4 = True,
      grid_interval = (0.2, 0.2),
      plot_title = base_name,
      date_format = 'YYYY-MM-dd',
      fig_size = (10, 10),
      dpi_plot = 100,
      file_format = "png",
      north_arrow_dict = self.north_arrow_dict1,
      scale_bar_dict = self.scale_bar_dict1,
      verbose = True,
    )

  def create_imagery(self):
    base_name_list = self.bases['Name'].tolist()
    self.generate_timeseries_gif(base_name, start_date, end_date, outpath)

if __name__ == '__main__':
  cartoee.get_image_collection_gif = new_get_image_collection_gif
  sar = SAREXPLORER()
  sar.run()