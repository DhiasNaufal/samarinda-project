import ee

def authenticate_and_initialize(project):
    """Authenticate and initialize the Google Earth Engine."""
    ee.Authenticate()
    ee.Initialize(project=project)
    print("GEE Authentication Successful")
    
def authenticate_gee(self):
    self.project = self.project_input.text().strip()

    if not self.project:
        self.log("Error: Please enter a project name before authentication!")
        return
    try:
        authenticate_and_initialize(self.project)
        self.log(f"Authenticated with project: {self.project}")
    except Exception as e:
        self.log(f"Authentication failed: {str(e)}")