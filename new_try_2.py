from landsatxplore.earthexplorer import EarthExplorer

username = 'Panicia'
password = 'f4h83nfjfdilJJJjjj'

ee = EarthExplorer(username, password)

ee.download('LT51960471995178MPS00', output_dir='D:\\experiment\\')

ee.logout()