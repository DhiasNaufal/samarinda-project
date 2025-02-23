import ee

def authenticate_and_initialize(project):
    """Authenticate and initialize the Google Earth Engine."""
    ee.Authenticate()
    ee.Initialize(project=project)
    print("GEE Authentication Successful")
