const SET_COMPONENT_VALUE = 'streamlit:setComponentValue';
const RENDER = 'streamlit:render';
const COMPONENT_READY = 'streamlit:componentReady';
const SET_FRAME_HEIGHT = 'streamlit:setFrameHeight';

function _sendMessage(type, data) {
  // copy data into object
  var outboundData = Object.assign(
    {
      isStreamlitMessage: true,
      type: type,
    },
    data
  );

  if (type == SET_COMPONENT_VALUE) {
    console.log('_sendMessage data: ' + JSON.stringify(data));
    console.log('_sendMessage outboundData: ' + JSON.stringify(outboundData));
  }

  window.parent.postMessage(outboundData, '*');
}

function initialize(pipeline) {
  // Hook Streamlit's message events into a simple dispatcher of pipeline handlers
  window.addEventListener('message', (event) => {
    if (event.data.type == RENDER) {
      // The event.data.args dict holds any JSON-serializable value
      // sent from the Streamlit client. It is already deserialized.
      pipeline.forEach((handler) => {
        handler(event.data.args);
      });
    }
  });

  _sendMessage(COMPONENT_READY, { apiVersion: 1 });

  // Component should be mounted by Streamlit in an iframe, so try to autoset the iframe height.
  window.addEventListener('load', () => {
    window.setTimeout(function () {
      setFrameHeight(document.documentElement.clientHeight);
    }, 0);
  });
}

function setFrameHeight(height) {
  _sendMessage(SET_FRAME_HEIGHT, { height: height });
}

// The `data` argument can be any JSON-serializable value.
function notifyHost(data) {
  _sendMessage(SET_COMPONENT_VALUE, data);
}

// custom component code
(function () {
  var map = L.map('map').setView([51.004, 37.111], 5);

  // osm layer (topo)
  var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>',
  });
  // esri layer (sat)
  var esri = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: 'Powered by <a href="https://www.esri.com/">Esri</a>'
  });
  // combine the layers
  var baseMaps = {
    "OpenStreetMap": osm,
    "EsriWorldImagery": esri
  };
  // set default layer
  osm.addTo(map);
  // add layer control (default: topright)
  L.control.layers(baseMaps).addTo(map);
  // show the scale bar on the lower left corner
  L.control.scale({ imperial: true, metric: true, position: 'bottomleft' }).addTo(map);

  var layerGroup = L.layerGroup().addTo(map);

  map.on('click', function (ev) {
    layerGroup.clearLayers();
    var latlng = map.mouseEventToLatLng(ev.originalEvent);
    L.marker([latlng.lat, latlng.lng]).addTo(layerGroup);
    notifyHost({
      value: [latlng.lat, latlng.lng],
      dataType: 'json',
    });
  });
})();

// ----------------------------------------------------
// Finally, initialize component passing in pipeline
initialize([]);
