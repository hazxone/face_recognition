import face_recognition
import time
import uuid
from flask import Flask, jsonify, request, redirect, make_response
import os.path
from collections import Counter
import random
import pickle
import os
import numpy as np
from data.L6SOsgE6HT import users
import database_
from functools import lru_cache
#import flask_profiler

from flask_httpauth import HTTPBasicAuth
import flask_monitoringdashboard as dashboard

auth = HTTPBasicAuth()

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
dashboard.config.init_from(file='config.cfg')
dashboard.bind(app)
#app.config["DEBU"] = True #flask profiler

# You need to declare necessary configuration to initialize #flask profiler
# flask-profiler as follows:
# app.config["flask_profiler"] = {
#     "enabled": app.config["DEBU"],
#     "storage": {
#         "engine": "sqlite"
#     },
#     "basicAuth":{
#         "enabled": True,
#         "username": "admin",
#         "password": "admin"
#     },
#     "ignore": [
# 	    "^/static/.*"
# 	]
# }

pickle_name = "blank.p"

@lru_cache(maxsize=4)
def load_pickle(pickle_name):
    if os.path.isfile(pickle_name):
        with open(pickle_name, "rb") as f:
            data = pickle.load(f)
    else:
        data = {}
    return data

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.get_password
def get_password(username):
    if username in users:
        return users.get(username)
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'Error':'Unauthorized Access'}), 403)

@app.route('/compare', methods=['POST'])
@auth.login_required
def compare():
    company = auth.username()
    unique_id = uuid.uuid4()
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'image_2' not in request.files:
            return redirect(request.url)

        image_1 = request.files['image_1']
        image_2 = request.files['image_2']
        if 'image_3' in request.files:
            image_3 = request.files['image_3']
        else:
            image_3 = None

        if image_1.filename == '' and image_2.filename == '':
            return redirect(request.url)

        if image_1 and allowed_file(image_1.filename) and image_2 and allowed_file(image_2.filename):
            return detect_faces_in_image(image_1, image_2, company, unique_id, image_3)

    # If no valid image file was uploaded, show the file upload form:
    result = {"Status" : "Data Handling Error"}
    database_.store_sqlite(company, unique_id, "compare", result)
    return jsonify(result)
    #'''
    # <!doctype html>
    # <title>Alphaface</title>
    # <h1>Upload pictures</h1>
    # <form method="POST" enctype="multipart/form-data">
    #   <input type="file" name="file">
    #   <input type="file" name="file2">
    #   <input type="submit" value="Upload">
    # </form>
    # '''

@app.route('/register', methods=['POST'])
@auth.login_required
def register_image():
    # Check if a valid image file was uploaded
    company = auth.username()
    unique_id = uuid.uuid4()
    if request.method == 'POST':
        if 'image_1' not in request.files:
            return redirect(request.url)

        image_1 = request.files['image_1']
        name = request.form['name']
        pickle_name = "data/" +company + ".p"
        overwrite = True

        if overwrite == request.form['overwrite']:
            overwrite = False

        if image_1.filename == '':
            return redirect(request.url)

        data = load_pickle(pickle_name)
        # if os.path.isfile(pickle_name):
        #     with open(pickle_name, "rb") as f:
        #         data = pickle.load(f)
        # else:
        #     data = {}

        encoding = load_crop_encode(image_1)

        list_names = list(data.keys())

        if name in list_names and overwrite == False:
            name = name + "_" + str(random.randint(101, 999))
            data[name] = encoding

        elif name in list_names and overwrite == True:
            data[name] = encoding

        else:
            data[name] = encoding

        with open(pickle_name, 'wb') as f:
            pickle.dump(data, f)

        result = { "Status" : "Successfully Add New Entry", "UUID": unique_id}
        database_.store_sqlite(company, unique_id, "register", result)
        return jsonify(result)
    result = {"Status" : "Error", "Message" : "No Entry Added to Database"}
    database_.store_sqlite(company, unique_id, "register", result)
    return jsonify(result)


@app.route('/verify', methods=['POST'])
@auth.login_required
def verify_image():
    company = auth.username()
    unique_id = uuid.uuid4()
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'image_1' not in request.files:
            return redirect(request.url)

        image_1 = request.files['image_1']
        pickle_name = "data/" + company + ".p"

        if image_1.filename == '':
            return redirect(request.url)

        # if os.path.isfile(pickle_name):
        #     with open(pickle_name, "rb") as f:
        #         data = pickle.load(f)
        # else:
        #     data = {}
        data = load_pickle(pickle_name)

        face_names = list(data.keys())
        face_encodings = np.array(list(data.values()))

        unknown_encoding = load_crop_encode(image_1)

        result = face_recognition.compare_faces(face_encodings, unknown_encoding)

        verify = (Counter(result))
        if (verify[True]) == 1:
        	for face_names, result in zip(face_names, result) :
        		if result == True:
        			recognize = "Match Found"
        			json_name = face_names

        elif (verify[True]) == 0:
        	json_name = "Unknown"
        	recognize = "No Match Found"

        else:
            json_name = "Found more than 1 face matched"
            recognize = "Failed"

        result = {
            "Identity": json_name,
            "Status": recognize,
            "UUID": unique_id
        }
        output = {"Identity": json_name, "Status": recognize,}
        database_.store_sqlite(company, unique_id, "verify", output)
        return jsonify(result)
    result = {"Status" : "Data Handling Error"}
    database_.store_sqlite(company, unique_id, "verify", result)
    return jsonify(result)

def load_crop_encode(file):
    img_lce = face_recognition.load_image_file(file)
    face_location_lce = face_recognition.face_locations(img_lce)
    top_lce, right_lce, bottom_lce, left_lce = face_location_lce[0]
    face_crop_lce = img_lce[(top_lce):(bottom_lce), (left_lce):(right_lce)]
    encoding_lce = face_recognition.face_encodings(face_crop_lce)[0]
    return encoding_lce


def detect_faces_in_image(file_stream_1, file_stream_2, company, unique_id, file_stream_3 = None):
    # Load the uploaded image file
    face_1_enc = load_crop_encode(file_stream_1)
    face_2_enc = load_crop_encode(file_stream_2)
    if file_stream_3:
        face_3_enc = load_crop_encode(file_stream_3)

    epoch = time.time()
    unique_id = uuid.uuid4()
    unique_id = "%s_%d" % (unique_id, epoch)

    #pil_image_1 = Image.fromarray(face_crop_1)
    #pil_image_2 = Image.fromarray(face_crop_2)
    #pil_image_1.save(unique_id + '_1.jpg')
    #pil_image_2.save(unique_id + '_2.jpg')

    face_found = False
    is_match = False

    if len(face_2_enc) > 0 and len(face_1_enc) > 0 and file_stream_3 == None:
        face_found = True
        # See if the first face in the uploaded image matches the known face
        match_results = face_recognition.compare_faces([face_1_enc], face_2_enc)
        if match_results[0]:
            is_match = True
    else:
        match_results_1 = face_recognition.compare_faces([face_1_enc], face_2_enc)
        match_results_2 = face_recognition.compare_faces([face_1_enc], face_3_enc)
        if match_results_1[0] and match_results_2[0]:
            is_match = True

    # Return the result as json
    result = {
        "Status": is_match,
        "UUID": unique_id
    }
    output = {"Status": is_match}
    database_.store_sqlite(company, unique_id, "compare", output)
    return jsonify(result)

#flask_profiler.init_app(app) #flask profiler

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
