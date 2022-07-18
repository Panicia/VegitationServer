#https://github.com/yannforget/landsatxplore/discussions/34

import json
import requests
import sys
import time
import argparse
import os
import pandas as pd
import getpass
import logging

# send http request
def sendRequest(url, data, apiKey = None):
    json_data = json.dumps(data)

    if apiKey == None:
        response = requests.post(url, json_data)
    else:
        headers = {'X-Auth-Token': apiKey}
        response = requests.post(url, json_data, headers = headers)

    try:
      httpStatusCode = response.status_code
      if response == None:
          print("No output from service")
          sys.exit()
      output = json.loads(response.text)
      if output['errorCode'] != None:
          print(output['errorCode'], "- ", output['errorMessage'])
          sys.exit()
      if  httpStatusCode == 404:
          print("404 Not Found")
          sys.exit()
      elif httpStatusCode == 401:
          print("401 Unauthorized")
          sys.exit()
      elif httpStatusCode == 400:
          print("Error Code", httpStatusCode)
          sys.exit()
    except Exception as e:
          response.close()
          print(e)
          sys.exit()
    response.close()

    return output['data']


def downloadData(outDir: str, orderID: str):
    """
    Download the data
    :param outDir: Full path to the order download folder
    :param orderID: Order download URL and ID
    :return:
    """

    if not os.path.exists(outDir):
        os.makedirs(outDir)

    t = time.time()

    orderURL = orderID['link']

    try:

        resp = requests.get(orderURL, stream=True)

        if resp.status_code == "ordered" or resp.status_code == 200:

            prodID = resp.headers['Content-Disposition'].split('"')[1]

            filename = outDir + os.sep + prodID

            # Only download data that don't already exist
            if not os.path.exists(filename):

                logging.info(f"Downloading orderID: {orderID['sceneID']} ProdID {prodID}")

                with open(filename, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=2048):
                        f.write(chunk)

                    if os.path.exists(filename):
                        logging.info(os.path.getsize(filename) / 1024 / (time.time() - t) / 1024)

            else:
                logging.warning(f"orderID: {orderID['sceneID']} already exists - ProdID {prodID}")

        else:
            logging.warning(f"Could not download {orderID['sceneID']}")

            logging.warning(f"Error {str(resp.status_code)}")

    except Exception as e:
        logging.error(f"Exception ecncountered while downloading {orderID['sceneID']}. The exception message: {e}")



    return None

def ERSlogin() -> str:
    """
    Get ERS password using command-line input
    :return:
    """
    return getpass.getpass("Enter ERS password: ")


if __name__ == '__main__':
    #NOTE :: Passing credentials over a command line arguement is not considered secure
    #        and is used only for the purpose of being example - credential parameters
    #        should be gathered in a more secure way for production usage
    #Define the command line arguements

    # user input
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True, help='Username')
    #parser.add_argument('-p', '--password', required=True, help='Password')

    args = parser.parse_args()

    username = args.username
    #password = args.password
    password = getpass.getpass('Enter ERS password: ')


    serviceUrl = "https://m2m.cr.usgs.gov/api/api/json/stable/"

    # login
    loginParameters = {'username' : username, 'password' : password}

    apiKey = sendRequest(serviceUrl + "login", loginParameters)

    # Do not print API key
    # logging.ifno("API Key: " + apiKey + "\n");

    datasetName = "landsat_ot_c2_l1"
    inDir = r'/data3/sarab/m2m'
    outDir = r'/espa-storage/downloads/acix2scenes/c2l1'
    #inDir = r'D:\22 Cloud Works\10 M2M\M2M download'

    # enable logging
    log_Out = inDir + os.sep + f"download_scenes_log_{time.strftime('%Y%m%d-%I%M%S')}.log"
    logging.basicConfig(filename=log_Out, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Create a dataframe from csv
    sceneList = pd.read_csv(inDir + os.sep+ 'GSFC_scene_list.csv', delimiter='\n')


    datasetSearchParameters = {'datasetName' : datasetName}

    logging.info("Searching datasets...")
    datasets = sendRequest(serviceUrl + "dataset-search", datasetSearchParameters, apiKey)

    logging.info(f"Found {len(datasets)} datasets");

    # download datasets
    for dataset in datasets:

        # Skip any other datasets that might be found
        if dataset['datasetAlias'] != datasetName:
            logging.info("Found dataset " + dataset['collectionName'] + " but skipping it.");
            continue;



        # Run a scene search to find data to download
        logging.info("Searching scenes...");

        sceneIds = sceneList['SceneID'].tolist()


        # Find the download options for these scenes
        # NOTE :: Remember the scene list cannot exceed 50,000 items!
        downloadOptionsParameters = {'datasetName' : dataset['datasetAlias'],
                                     'entityIds' : sceneIds}

        downloadOptions = sendRequest(serviceUrl + "download-options", downloadOptionsParameters, apiKey)

        # Aggregate a list of available products
        downloads = []
        for product in downloadOptions:
                # Make sure the product is available for this scene
                if product['available'] == True and product['productName'] == 'Landsat Collection 2 Level-1 Product Bundle':
                     downloads.append({'entityId' : product['entityId'],
                                       'productId' : product['id']})

        # Did we find products?
        if downloads:
            requestedDownloadsCount = len(downloads)
            # set a label for the download request
            label = "download-data"
            downloadRequestParameters = {'downloads' : downloads,
                                         'label' : label}
            # Call the download to get the direct download urls
            requestResults = sendRequest(serviceUrl + "download-request", downloadRequestParameters, apiKey)

            # PreparingDownloads has a valid link that can be used but data may not be immediately available
            # Call the download-retrieve method to get download that is available for immediate download
            orderids = []
            if requestResults['preparingDownloads'] != None and len(requestResults['preparingDownloads']) > 0:
                downloadRetrieveParameters = {'label' : label}
                moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", downloadRetrieveParameters, apiKey)

                downloadIds = []


                for download in moreDownloadUrls['available']:
                    downloadIds.append(download['downloadId'])
                    orderids.append({'sceneID': download['entityId'], 'link':download['url']})

                for download in moreDownloadUrls['requested']:
                    downloadIds.append(download['downloadId'])
                    orderids.append({'sceneID': download['entityId'], 'link':download['url']})


                # Didn't get all of the reuested downloads, call the download-retrieve method again probably after 30 seconds
                while len(downloadIds) < requestedDownloadsCount:
                    preparingDownloads = requestedDownloadsCount - len(downloadIds)
                    logging.warning(preparingDownloads, "downloads are not available. Waiting for 30 seconds.")
                    time.sleep(30)
                    logging.info("Trying to retrieve data")
                    moreDownloadUrls = sendRequest(serviceUrl + "download-retrieve", downloadRetrieveParameters, apiKey)
                    for download in moreDownloadUrls['available']:
                        if download['downloadId'] not in downloadIds:
                            downloadIds.append(download['downloadId'])
                            orderids.append({'sceneID': download['entityId'], 'link':download['url']})

            else:
                # Get all available downloads
                for download in requestResults['availableDownloads']:

                    orderids.append({'sceneID': download['downloadId'], 'link':download['url']})
            logging.info("All downloads are available to download.")


        # Download the search results

        for orderid in orderids:
            logging.info(f"Working on order ID {orderid['sceneID']}.")

            downloadData(outDir, orderid)

        logging.info(f"Downloaded files can be found at {outDir}")

    # Logout so the API Key cannot be used anymore
    endpoint = "logout"
    if sendRequest(serviceUrl + endpoint, None, apiKey) == None:
        logging.warning("Logged Out\n\n")
    else:
        logging.error("Logout Failed\n\n")

    logging.warning("All done.")
    logging.shutdown()