TILE_PROVIDERS = [
  {
    "name": "Google Satellite",
    "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "zoom_level": [str(zoom) for zoom in range(15, 21)]
  },
  {
    "name": "ArcGIS World Imagery",
    "url": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "zoom_level": [str(zoom) for zoom in range(15, 20)]
  },
  {
    "name": "Bing Maps", 
    "url": "https://t0.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=5179",
    "zoom_level": [str(zoom) for zoom in range(15, 20)]
  }
]