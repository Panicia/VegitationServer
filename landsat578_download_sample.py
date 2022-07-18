from landsat.google_download import GoogleDownload

'''g = GoogleDownload(start='2022-05-01',
                    end='2022-06-30',
                    satellite=8,
                    latitude='64.54004899431433',
                    longitude='40.515813383105126',
                    max_cloud_percent=30,
                    output_path='D:\\experiment\\')'''
g = GoogleDownload(start='2021-05-01',
                    end='2021-06-30',
                    satellite=8,
                    path='38', row='28',
                    max_cloud_percent=30,
                    output_path='D:\\experiment\\')
g.candidate_scenes()