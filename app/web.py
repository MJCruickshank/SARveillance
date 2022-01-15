import streamlit as st
import os
import datetime
import base64
import geemap as gee
import pandas as pd
from imagery import Imagery
from map import map_component

# page config
st.set_page_config(page_title="SARveillance", page_icon="🛰️")

class SARVEILLANCE():

  def __init__(self):
    self.gee = gee
    self.bases = []
    self.poi = None
    self.imagery = None
    # ugly attempt to get the data folder path
    self.outpath = os.path.abspath(os.path.join(__file__, '..', '..', 'data'))
    self.max_frames=20

  def run(self):
    self.setup_gee()
    self.load_bases()
    self.init_imagery()
    self.init_gui()

  def setup_gee(self):
    # self.gee.ee.Authenticate()
    self.gee.ee_initialize()


  def load_bases(self):
    # load csv data with places of interest
    self.bases = pd.read_csv("poi/poi_df.csv")

  def init_imagery(self):
    self.imagery = Imagery()
    self.imagery.get_collection()

  def create_poi(self, type, name, start_date, end_date, lat=None, lon=None):
    if type == 'preset':
      poi_data = self.bases.loc[self.bases['Name'] == name]
      self.poi = {
        'name': name,
        'lat': poi_data['lat'].values[0],
        'lon': poi_data['lon'].values[0],
        'start_date': start_date,
        'end_date': end_date
      }
    elif type == 'custom':
      try:
        float(lat)
        float(lon)
      except ValueError:
        st.error('Latitude & Longitude must be numeric values!')
        st.stop()
      self.poi = {
        'name': name,
        'lat': float(lat),
        'lon': float(lon),
        'start_date': start_date,
        'end_date': end_date
      }
    else:
      st.error('Error')

  def load_custom_css(self):
    with open('app/custom.css') as f:
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

    # preset poi select (form element)
    preset_name = st.selectbox('Which location would you like to examine?', poi_list, key='poi_select')

    # expander with a map to pick coordinates and to enter a custom name
    with st.expander("Custom Location (overrides a selected location)"):
      # columns with inputs for name, lat & lon
      col_custom_name, col_lat, col_lon = st.columns(3)
      with col_custom_name:
        custom_name = st.text_input('Location name', '', placeholder='custom name')
      with col_lat:
        lat_input = st.empty()
        lat = lat_input.text_input('Latitude (enter or click map)', '', placeholder='latitude')
      with col_lon:
        lon_input = st.empty()
        lon = lon_input.text_input('Longitude (enter or click map)', '', placeholder='longitude')

      # call map component and watch for return values
      coordinates = map_component(key='map')
      if coordinates:
        lat = lat_input.text_input('Select Latitude', value=coordinates[0])
        lon = lon_input.text_input('Select Longitude', value=coordinates[1])

    # date picker for start & end date (form element)
    today = datetime.date.today()
    lastweek = (today - datetime.timedelta(days=7))
    col_start_date, col_end_date = st.columns(2)
    with col_start_date:
      start_date = st.date_input('Start Date', lastweek)
    with col_end_date:
      end_date = st.date_input('End Date', today)
    # format the dates and set class variables
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    if custom_name != '' and lat != '' and lon != '':
      self.create_poi('custom', custom_name, start_date, end_date, lat, lon)
    elif preset_name != None and preset_name != '---':
      self.create_poi('preset', preset_name, start_date, end_date)
    else:
      st.error('Choose a location first!')
      st.stop()

    if self.poi:
      st.markdown(f"<div class='st-ae st-af st-ag st-ah st-ai st-aj st-ak st-al st-am st-b8 st-ao st-ap st-aq st-ar st-as st-at st-au st-av st-aw st-ax st-ay st-az st-b9 st-b1 st-b2 st-b3 st-b4 st-b5 st-b6' style='flex-direction: column;'><h6>Location: {self.poi['name']}</h6>Coordinates: [{self.poi['lat']}, {self.poi['lon']}]<br />Timespan: {self.poi['start_date']} - {self.poi['end_date']}</div><br />", unsafe_allow_html=True)

      # on submit
      if st.button('Generate SAR Timeseries'):
        self.generate()


  def generate(self):
    with st.spinner('Loading timeseries... this may take a couple of minutes'):
      self.imagery.set_poi(self.poi, self.outpath)
      (err, msg) = self.imagery.generate_timeseries_gif(max_frames=self.max_frames)

    if err:
      st.error(msg)
      st.stop()
    else:
      st.success('Done!')
      self.display_gif()
      self.show_download()

  def display_gif(self):
    # poi data
    base_name = self.poi['name']
    base_path = os.path.join(self.outpath, 'BaseTimeseries', base_name)
    if not os.path.exists(base_path):
      os.makedirs(base_path)
    gif_loc = f'{base_path}/{base_name}.gif'
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
    base_path = os.path.join(self.outpath, 'BaseTimeseries', base_name)
    if not os.path.exists(base_path):
      os.makedirs(base_path) 
    gif_loc = f'{base_path}/{base_name}.gif'

    with open(gif_loc, "rb") as file:
      btn = st.download_button(
        label="Download image",
        data=file,
        file_name="timeseries.gif",
        mime="image/gif"
        )


if __name__ == '__main__':
  # overwrite cartoee method 
  # cartoee.get_image_collection_gif = new_get_image_collection_gif
  # start a new class instance with the run() method
  sar = SARVEILLANCE()
  sar.run()