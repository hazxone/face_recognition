import face_recognition
import time
import uuid
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

        rules = [file == True, allowed_file(file.filename) == True, file2 == True, allowed_file(file2.filename) == True]
        if all(rules):
        #if file and allowed_file(file.filename) and file2 and allowed_file(file2.filename):
            # The image file seems valid! Detect faces and return the result.
            return detect_faces_in_image(file, file2)

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

    top_1, right_1, bottom_1, left_1 = face_location_1[0]
    top_2, right_2, bottom_2, left_2 = face_location_2[0]

    face_crop_1 = img_1[top_1:bottom_1, left_1:right_1]
    face_crop_2 = img_2[top_2:bottom_2, left_2:right_2]

    face_1_enc = face_recognition.face_encodings(face_crop_1)[0]
    face_2_enc = face_recognition.face_encodings(face_crop_2)[0]

    epoch = time.time()
    user_id = uuid.uuid4() # this could be incremental or even a uuid
    unique_id = "%s_%d" % (user_id, epoch)
    print(unique_id)

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
        "Status": is_match
    }
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
