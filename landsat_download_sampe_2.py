from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer

import json

# Initialize a new API instance and get an access key
username = 'Panicia'
password = 'f4h83nfjfdilJJJjjj'

api = API(username, password)

scenes = api.search(
    dataset = 'landsat_ot_c2_l2',
    latitude = 64.53840324293397,
    longitude = 40.51387956369441,
    start_date = '2022-05-01',
    end_date = '2022-06-30',
    max_cloud_cover = 10
)

print(f"{len(scenes)} scenes found.")

# Process the result
for scene in scenes:
    print(scene['acquisition_date'].strftime('%Y-%m-%d'))
    # Write scene footprints to disk
    fname = f"{scene['landsat_product_id']}.geojson"
    with open(fname, "w") as f:
        json.dump(scene['spatial_coverage'].__geo_interface__, f)

api.logout()


ee = EarthExplorer(username, password)

ee.download(scenes[0], output_dir='D:\\experiment\\')

ee.logout()