import streamlit as st
import os
import datetime
import ee
import sys
import base64
import geemap as gee
from geemap import cartoee
import pandas as pd
from utils import new_get_image_collection_gif

class SAREXPLORER():

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
    self.poi = None
    self.col_final = None
    self.dirname = os.path.dirname(__file__)
    self.outpath = self.dirname+"/Data/"

  def run(self):
    self.auth()
    self.load_bases()
    self.init_gui()

  def auth(self):
    # self.gee.ee.Authenticate()
    self.gee.ee_initialize()

  def load_bases(self):
    # load csv data with places of interest
    self.bases = pd.read_csv("bases_df.csv")


  def create_poi(self, type, name, lat=None, lon=None):
    if type == 'preset':
      poi_data = self.bases.loc[self.bases['Name'] == name]
      self.poi = {
        'name': name,
        'lat': poi_data['lat'].values[0],
        'lon': poi_data['lon'].values[0]
      }
    elif type == 'custom':
      if not lat.isnumeric() or not lon.isnumeric():
        st.error('Latitude & Longitude must be numeric values!')
        st.stop()
      self.poi = {
        'name': name,
        'lat': float(lat),
        'lon': float(lon)
      }
    else:
      st.error('Error')

  def load_custom_css(self):
    with open('custom.css') as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

  def init_gui(self):
    # load custom css
    self.load_custom_css()
    # prepare initial form data
    poi_list = self.bases['Name'].tolist()
    poi_list.insert(0, '---')

    # header
    st.title('SARveillance')
    st.subheader('Sentinel-1 SAR time series analysis for OSINT use')
    # preset poi select
    poi = st.selectbox('Which location would you like to examine?', poi_list)
    # custom poi
    with st.expander("Custom Location"):
      # st.map(data=None, zoom=None, use_container_width=True)
      col_lat, col_lon = st.columns(2)
      with col_lat:
        lat = st.text_input('Select Latitude', '')
      with col_lon:
        lon = st.text_input('Select Longitude', '')
    # date picker for start & end date
    today = datetime.date.today()
    lastweek = (today - datetime.timedelta(days=7))
    col_start_date, col_end_date = st.columns(2)
    with col_start_date:
      start_date = st.date_input('Start Date', lastweek)
    with col_end_date:
      end_date = st.date_input('End Date', today)
    # format the dates and set as class variables
    self.start_date = start_date.isoformat()
    self.end_date = end_date.isoformat()
    # Submit
    if st.button('Generate SAR Timeseries', key="submit"):
      if lat != '' and lon != '':
        self.create_poi('custom', 'Custom', lat, lon)
      elif poi != None and poi != '---':
        self.create_poi('preset', poi)
      else:
        st.error('Choose a location first!')
        st.stop()
      # we have a valid poi
      st.info(f"Generating time series for {self.poi['name']} ({self.poi['lat']},{self.poi['lon']})")
      self.generate()

  def generate(self):
    self.get_collection()
    with st.spinner('Loading timeseries... this may take a couple of minutes'):
      self.generate_timeseries_gif()
    st.success('Done!')
    self.display_gif()
    self.show_download()
  
  def get_collection(self):
    collection = ee.ImageCollection('COPERNICUS/S1_GRD')
    collection_both = collection.filter(ee.Filter.listContains(
        'transmitterReceiverPolarisation', 'VV')).filter(ee.Filter.eq('instrumentMode', 'IW'))
    # composite_col = collection_both.map(lambda image: image.select(
    #     "VH").subtract(image.select("VH")).rename("VH-VV"))
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

  def display_gif(self):
    # poi data
    base_name = self.poi['name']

    gif_loc = os.path.expanduser(self.outpath+"BaseTimeseries/"+base_name+"/"+base_name + ".gif")
    file_ = open(gif_loc, "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()
    st.markdown(
    f'<img align="left" width="704" height="704" src="data:image/gif;base64,{data_url}" alt="Base Timeseries">',
    unsafe_allow_html=True)

  def show_download(self):
    # poi data
    base_name = self.poi['name']   

    gif_loc = os.path.expanduser(self.outpath+"BaseTimeseries/"+base_name+"/"+base_name + ".gif")
    with open(gif_loc, "rb") as file:
      btn = st.download_button(
        label="Download image",
        data=file,
        file_name="timeseries.gif",
        mime="image/gif"
        )


if __name__ == '__main__':
  # overwrite cartoee method 
  cartoee.get_image_collection_gif = new_get_image_collection_gif
  # start a new class instance with the run() method
  sar = SAREXPLORER()
  sar.run()