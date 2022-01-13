import ee
from geemap import cartoee
from utils import new_get_image_collection_gif

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

  def __init__(self, gee, poi):
    cartoee.get_image_collection_gif = new_get_image_collection_gif
    self.gee = gee
    self.poi = poi

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

  def generate_timeseries_gif(self):
    # poi data
    base_name = self.poi['name']
    lat = self.poi['lat']
    lon = self.poi['lon']
    # prepare collection
    self.get_collection()
    # filter
    col_final_recent = self.col_final.filterDate(self.start_date, self.end_date) 
    col_filtered = self.get_filtered_col(col_final_recent, base_name).sort("system:time_start")
    aoi = self.generate_base_aoi()
    minmax = col_filtered.first().reduceRegion(ee.Reducer.minMax(), aoi)
    max = minmax.getNumber("VV_max").getInfo()
    min = minmax.getNumber("VV_min").getInfo()
    w = 0.4
    h = 0.4
    region = [lon+w, lat-h, lon-w, lat+h]
    out_dir = os.path.expanduser(self.outpath)
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
      ee_ic = col_filtered,
      out_dir = os.path.expanduser(self.outpath+"BaseTimeseries/"+base_name+"/"),
      out_gif = base_name + ".gif",
      vis_params = visParams,
      region = region,
      fps = 2,
      mp4 = False,
      grid_interval = (0.2, 0.2),
      plot_title = base_name,
      date_format = 'YYYY-MM-dd',
      fig_size = (10, 10),
      dpi_plot = 100,
      file_format = "png",
      north_arrow_dict = self.north_arrow_dict1,
      verbose = True,
    )