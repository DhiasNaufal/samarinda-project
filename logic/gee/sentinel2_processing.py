import ee

def mask_clouds(img: ee.image, max_cloud_prob: int) -> ee.image:
    """Masking clouds based on cloud probability."""
    clouds = ee.Image(img.get("cloud_mask")).select("probability")
    is_not_cloud = clouds.lt(max_cloud_prob)
    return img.updateMask(is_not_cloud)

def mask_edges(s2_img: ee.image) -> ee.image:
    """Masking image edges where there is no valid data."""
    return s2_img.updateMask(
        s2_img.select("B8A").mask().updateMask(s2_img.select("B9").mask())
    )

def process_sentinel2(
        geometry: ee.geometry, 
        start_date: str, 
        end_date: str, 
        max_cloud_prob: int) -> ee.image:
    """Process Sentinel-2 data with cloud masking and clipping."""
    # Load Sentinel-2 dataset
    s2_sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    s2_clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
    
    # Filter datasets based on date and geometry
    criteria = ee.Filter.bounds(geometry).And(ee.Filter.date(start_date, end_date))
    s2_sr_filtered = s2_sr.filter(criteria).map(mask_edges)
    s2_clouds_filtered = s2_clouds.filter(criteria)
    
    # Join cloud probability dataset with Sentinel-2 surface reflectance dataset
    join = ee.Join.saveFirst("cloud_mask")
    condition = ee.Filter.equals(leftField="system:index", rightField="system:index")
    s2_sr_with_cloud_mask = join.apply(s2_sr_filtered, s2_clouds_filtered, condition)
    
    # Apply cloud masking and create a median composite
    s2_cloud_masked = ee.ImageCollection(s2_sr_with_cloud_mask).map(lambda img: mask_clouds(img, max_cloud_prob)).median()
    
    # Clip the image to the selected geometry
    s2_clipped = s2_cloud_masked.clip(geometry)
    
    return s2_clipped
