import face_recognition
import time
import uuid
from flask import Flask, jsonify, request, redirect
import os.path
from collections import Counter
import random
import pickle
import os
import numpy as np

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
pickle_name = "med2.p"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        file2 = request.files['file2']

        if file.filename == '' and file2.filename == '':
            return redirect(request.url)

        #rules = [file == True, allowed_file(file.filename) == True, file2 == True, allowed_file(file2.filename) == True]
        #if all(rules):
        #if file and allowed_file(file.filename) and file2 and allowed_file(file2.filename):
            # The image file seems valid! Detect faces and return the result.
        return detect_faces_in_image(file, file2)

    # If no valid image file was uploaded, show the file upload form:
    return '''
    <!doctype html>
    <title>Alphaface</title>
    <h1>Upload pictures</h1>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="file" name="file2">
      <input type="submit" value="Upload">
    </form>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        name = request.form['name']
        overwrite = request.form['overwrite']

        if overwrite:
            if overwrite == "False":
                overwrite = False
            else:
                overwrite = True
        else:
            overwrite = False

        if file.filename == '':
            return redirect(request.url)

        if os.path.isfile(pickle_name):
            with open(pickle_name, "rb") as f:
                data = pickle.load(f)
        else:
            data = {}

        encoding = load_crop_encode(file)

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

        result = { "Status" : "Successfully Add New Entry", "Directory" : os.path.isfile(pickle_name) }
        return jsonify(result)


@app.route('/verify', methods=['GET', 'POST'])
def verify_image():
    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if os.path.isfile(pickle_name):
            with open(pickle_name, "rb") as f:
                data = pickle.load(f)
        else:
            data = {}

        face_names = list(data.keys())
        face_encodings = np.array(list(data.values()))

        unknown_encoding = load_crop_encode(file)

        result = face_recognition.compare_faces(face_encodings, unknown_encoding)

        # recognize = False
        # Print the result as a list of names with True/False
        #names_with_result = list(zip(face_names, result))
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
        }
        return jsonify(result)

def load_crop_encode(file):
    img_lce = face_recognition.load_image_file(file)
    face_location_lce = face_recognition.face_locations(img_lce)
    top_lce, right_lce, bottom_lce, left_lce = face_location_lce[0]
    pad_y = int((bottom_lce - top_lce)*0.1)
    pad_x = int((right_lce - left_lce)*0.1)
    face_crop_lce = img_lce[(top_lce-pad_y):(bottom_lce+pad_y), (left_lce-pad_x):(right_lce+pad_x)]
    encoding_lce = face_recognition.face_encodings(face_crop_lce)[0]
    return encoding_lce

def detect_faces_in_image(file_stream_1, file_stream_2):
    # Load the uploaded image file
    face_1_enc = load_crop_encode(file_stream_1)
    face_2_enc = load_crop_encode(file_stream_2)

    epoch = time.time()
    user_id = uuid.uuid4() # this could be incremental or even a uuid
    unique_id = "%s_%d" % (user_id, epoch)
    #print(unique_id)

    #pil_image_1 = Image.fromarray(face_crop_1)
    #pil_image_2 = Image.fromarray(face_crop_2)
    #pil_image_1.save(unique_id + '_1.jpg')
    #pil_image_2.save(unique_id + '_2.jpg')

    face_found = False
    is_match = False

    if len(face_2_enc) > 0:
        face_found = True
        # See if the first face in the uploaded image matches the known face of Obama
        match_results = face_recognition.compare_faces([face_1_enc], face_2_enc)
        if match_results[0]:
            is_match = True

    # Return the result as json
    result = {
        "face_found_in_image": face_found,
        "Status": is_match,
        "UID": unique_id
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
