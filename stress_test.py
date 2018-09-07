# import the necessary packages
from threading import Thread
import requests
import time

# initialize the Keras REST API endpoint URL along with the input
# image path
KERAS_REST_API_URL = "http://198.13.53.125:4000"
IMAGE_PATH = "o1.jpg"
IMAGE_PATH_2 = "o2.jpg"

# initialize the number of requests for the stress test along with
# the sleep amount between requests
NUM_REQUESTS = 10
SLEEP_COUNT = 0.05

def call_predict_endpoint(n):
	# load the input image and construct the payload for the request
	image = open(IMAGE_PATH, "rb").read()
	image_2 = open(IMAGE_PATH_2, "rb").read()
	payload = {"file": image, "file2" : image_2}

	# submit the request
	r = requests.post(KERAS_REST_API_URL, files=payload).json()
	print(r)
	#ensure the request was sucessful
	if 'Status' in r:
	#if r["{'Status': True, 'face_found_in_image': True}"]:
		print("[INFO] thread {} OK".format(n))

	# otherwise, the request failed
	else:
		print("[INFO] thread {} FAILED".format(n))

# loop over the number of threads
for i in range(0, NUM_REQUESTS):
	# start a new thread to call the API
	t = Thread(target=call_predict_endpoint, args=(i,))
	t.daemon = True
	t.start()
	time.sleep(SLEEP_COUNT)

# insert a long sleep so we can wait until the server is finished
# processing the images
time.sleep(15)
