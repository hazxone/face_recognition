# This is a _very simple_ example of a web service that recognizes faces in uploaded images.
# Upload an image file and it will check if the image contains a picture of Barack Obama.
# The result is returned as json. For example:
#
# $ curl -XPOST -F "file=@obama2.jpg" -F "file2=trump.jpg" http://127.0.0.1:5001
#
# Returns:
#
# {
#  "face_found_in_image": true,
#  "is_picture_of_obama": true
# }
#
# This example is based on the Flask file upload example: http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

# NOTE: This example requires flask to be installed! You can install it with pip:
# $ pip3 install flask

import face_recognition
from flask import Flask, jsonify, request, redirect

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)


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
        
        rules = [file == True, allowed_file(file.filename) = True, file2 == True, allowed_file(file2.filename) == True]
        if all(rules):
        #if file and allowed_file(file.filename) and file2 and allowed_file(file2.filename):
            # The image file seems valid! Detect faces and return the result.
            return detect_faces_in_image(file)

    # If no valid image file was uploaded, show the file upload form:
    return '''
    <!doctype html>
    <title>Is this a picture of Obama?</title>
    <h1>Upload a picture and see if it's a picture of Obama!</h1>
    <form method="POST" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>
    '''


def detect_faces_in_image(file_stream_1, file_stream_2):
    # Load the uploaded image file
    img_1 = face_recognition.load_image_file(file_stream_1)
    img_2 = face_recognition.load_image_file(file_stream_2)
    
    face_locations_1 = face_recognition.face_locations(img_1)
    face_locations_2 = face_recognition.face_locations(img_2)
    
    top_1, right_1, bottom_1, left_1 = face_location_1
    top_2, right_2, bottom_2, left_2 = face_location_2
    
    face_crop_1 = img_1[top_1:bottom_1, left_1:right_1]
    face_crop_array_1 = Image.fromarray(face_crop_1)
    
    face_crop_2 = img_2[top_2:bottom_2, left_2:right_2]
    face_crop_array_2 = Image.fromarray(face_crop_2)
    
    face_1_enc = face_recognition.face_encodings(face_crop_array_1)[0]
    face_2_enc = face_recognition.face_encodings(face_crop_array_2)[0]
    
    
    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)

    face_found = False
    is_obama = False

    if len(unknown_face_encodings) > 0:
        face_found = True
        # See if the first face in the uploaded image matches the known face of Obama
        match_results = face_recognition.compare_faces([face_1_enc], face_2_enc)
        if match_results[0]:
            is_match = True

    # Return the result as json
    result = {
        "face_found_in_image": face_found,
        "Status": is_obama
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
