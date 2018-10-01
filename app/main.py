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
from sklearn.externals import joblib
#from knn import predict
#import flask_profiler
# from werkzeug import secure_filename
# filename = secure_filename(file.filename)

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

        if 'overwrite' in request.form:
            if request.form['overwrite'] == False:
                overwrite = False

        if image_1.filename == '':
            return redirect(request.url)

        data = load_pickle(pickle_name)

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

@app.route('/register_multiple', methods=['POST'])
#@auth.login_required
def register_multiple_image():
    company = request.form['company']
    unique_id = uuid.uuid4()
    if request.method == 'POST':
        name = request.form['name']
        app.config['UPLOAD_FOLDER'] = 'data/'+company+'/'+name+'/'
        uploaded_files = request.files.getlist("file[]")
        print(uploaded_files)
        #filenames = []
        for filename, file in request.files.iteritems():
            name = request.FILES[filename].name
            print(name)
        for index, file in enumerate(uploaded_files):
            # Check if the file is one of the allowed types/extensions
            if file and allowed_file(file.filename):
                # Make the filename safe, remove unsupported chars
                ##filename = secure_filename(file.filename)
                # Move the file form the temporal folder to the upload
                # folder we setup
                print(file)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Save the filename into a list, we'll use it later
                #filenames.append(filename)
                # Redirect the user to the uploaded_file route, which
                # will basicaly show on the browser the uploaded file
        # Load an html page with a link to each uploaded file
        #return render_template('upload.html', filenames=filenames)
    result = {"Status" : "Error", "Message" : "No Entry Added to Database"}
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

        data = load_pickle(pickle_name)

        face_names = list(data.keys())
        face_encodings = np.array(list(data.values()))

        unknown_encoding = load_crop_encode(image_1)

        result = face_recognition.compare_faces(face_encodings, unknown_encoding, tolerance=0.5)

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

@app.route('/verify_acc', methods=['POST'])
@auth.login_required
def verify__knn():
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

        knn_clf = None
        model_path="data/"+company+"_knn.clf"
        distance_threshold=0.5

        X_img_path = image_1
        if knn_clf is None:
            with open(model_path, 'rb') as f:
                knn_clf = pickle.load(f)

        # Load image file and find face locations
        X_img = face_recognition.load_image_file(X_img_path)
        X_face_locations = face_recognition.face_locations(X_img)

        # If no faces are found in the image, return an empty result.
        if len(X_face_locations) == 0:
            return []

        # Find encodings for faces in the test iamge
        faces_encodings = face_recognition.face_encodings(X_img, known_face_locations=X_face_locations)

        # Use the KNN model to find the best matches for the test face
        closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)
        are_matches = [closest_distances[0][i][0] <= distance_threshold for i in range(len(X_face_locations))]

        # Predict classes and remove classifications that aren't within the threshold
        #return [(pred, loc) if rec else ("unknown", loc) for pred, loc, rec in zip(knn_clf.predict(faces_encodings), X_face_locations, are_matches)]
        predictions = [(pred) if rec else ("Unknown") for pred, rec in zip(knn_clf.predict(faces_encodings), are_matches)]

        result = {"Identity": predictions[0]}

        database_.store_sqlite(company, unique_id, "verify_acc", result)
        return jsonify(result)

@app.route('/verify_svm', methods=['POST'])
@auth.login_required
def verify__svm():
    company = auth.username()
    unique_id = uuid.uuid4()
    start_time = time.time()
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'image_1' not in request.files:
            return redirect(request.url)

        image_1 = request.files['image_1']
        pickle_name = "data/" + company + ".p"

        if image_1.filename == '':
            return redirect(request.url)

        model_path="data/"+company+"_svm.p"

        X_img_path = image_1

        # Load image file and find face locations
        X_img = face_recognition.load_image_file(X_img_path)
        X_face_locations = face_recognition.face_locations(X_img)

        if len(X_face_locations) == 0:
            return []

        faces_encodings = face_recognition.face_encodings(X_img, known_face_locations=X_face_locations)

        # If no faces are found in the image, return an empty result.
        with open(model_path, 'rb') as infile:
            (model, class_names) = joblib.load(infile)

        predictions = model.predict_proba(faces_encodings)
        best_class_indices = np.argmax(predictions, axis=1)
        best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices] #: '%.3f' % best_class_probabilities[0]
        if best_class_probabilities[0] > 0.65:
            endtime = time.time()
            Time_taken = endtime - start_time
            result = {"Status" : "Success", "Identity" : class_names[best_class_indices[0]], "Time" : Time_taken}
        else:
            result = {"Status" : "Failed", "Identity" : "Unknown"}
        database_.store_sqlite(company, unique_id, "verify_svm", result)
        return jsonify(result)
    result = {"Status" : "Data Handling Error"}
    database_.store_sqlite(company, unique_id, "verify_svm", result)
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
        match_results = face_recognition.compare_faces([face_1_enc], face_2_enc, tolerance=0.5)
        if match_results[0]:
            is_match = True
    else:
        match_results_1 = face_recognition.compare_faces([face_1_enc], face_2_enc, tolerance=0.5)
        match_results_2 = face_recognition.compare_faces([face_1_enc], face_3_enc, tolerance=0.5)
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
    app.run(host='0.0.0.0', port=80, debug=True)
