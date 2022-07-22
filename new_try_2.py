from usgsm2m.api import M2M

username = 'Panicia'
password = 'f4h83nfjfdilJJJjjj'
datasetName = 'landsat_ot_c2_l2'

m2m = M2M(username, password, version = 'stable')

params = {
    "datasetName": datasetName,
    "startDate": "2020-08-01",
    "endDate": "2020-08-31",
    "geoJsonType": "Point",
    "geoJsonCoords": [64.53840324293397, 40.51387956369441],
    "maxCC": 10,
    "includeUnknownCC": False,
    "maxResults": 10
}
scenes = m2m.searchScenes(**params)
print("{} - {} hits - {} returned".format(datasetName,scenes['totalHits'],scenes['recordsReturned']))