from flask import Flask, jsonify, request, redirect, make_response, g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from werkzeug import secure_filename
import face_recognition as fr
from data.L6SOsgE6HT import users, tokens
import uuid
import cv2
import os
from web_utils import *
from flasgger import Swagger, swag_from
import yaml

# HTTP basic auth
# Two separate auth, one for username and password for generating token
# Second for token for API endpoint
basic_auth = HTTPBasicAuth()
auth = HTTPTokenAuth('Bearer') 
app = Flask(__name__, static_url_path='/static')
swagger = Swagger(app)

# Security Authentication ---------------------------
# Basic Username / Password
# Token generator : use username / password
# Save/Persist token as .token in pickle folder
@basic_auth.get_password
def get_password(username):
    if username in users:
        return users.get(username)
    return None

# Token dictionary is reverse {token:usename}, so its complicated to replace the value
# The loop is to find the key given the value(username)
# Then delete the key, reassign a new one
@app.route('/token', methods=['GET'])
@basic_auth.login_required
def generate_token():
    username = basic_auth.username()
    if username in users:
        for key, value in tokens.items():
            if value == username:
                new_token = gen_uuid()
                del tokens[key]
                tokens[new_token] = username
                save_pickle('session', 'token', tokens)
                result = {"Status" : "Changed", "New_Token" : new_token}
                return make_response(jsonify(result), 200)
    result = {"Status" : "Error", "Message" : "Wrong Credential"}
    return make_response(jsonify(result), 401)

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'Error':'Unauthorized Access'}), 401)

# Token Authentication for API endpoints
# All other endpoint except generate token use token auth

@auth.verify_token
def verify_token(token):
    g.user = None
    try:
        data = tokens
    except:
        return False
    if token in data:
        g.user = data[token]
        return True
    return False

# Endpoint to list all companies

@app.route('/companies', methods=['GET'])
@swag_from(yaml.load(open("companies.yml")))
@auth.login_required
def list_companies():
    c_list, _ = get_list_companies()
    return make_response(jsonify({'companies_id':c_list}), 200)

# Endpoint to list ic in company
# Argument : company id

@app.route('/companies/<companies_id>', methods=['GET'])
@auth.login_required
def list_users(companies_id):
    c_list, base_url = get_list_companies()
    ic_list = os.listdir(os.path.join(base_url,companies_id))
    
    if companies_id not in c_list:
        result = {"Status" : "Error", "Message" : "Companies not found"}
        return make_response(jsonify(result), 404)
    else:
        return make_response(jsonify({'companies_id':companies_id, 'ic_list':ic_list}), 200)

# Endpoint to add image
# Arguments : image, ic
# Search face and save at ./companies/ic/uuid.jpg

@app.route('/companies/<companies_id>', methods=['POST'])
@auth.login_required
def register_user(companies_id):        
    # Get request details
    initial = False
    if len(os.listdir('images')) == 0:
        initial = True

    else:
        if not os.path.isfile(os.path.join('pickle','X_y.npz')):
            result = {"Status" : "Error", "Message" : "Embeddings still not initialized"}
            return make_response(jsonify(result), 404)

    if request.method != 'POST':
        result = {"Status" : "Error", "Message" : "Method not allowed"}
        return make_response(jsonify(result), 405)

    image = request.files['image']

    if allowed_file(secure_filename(image.filename)) is False:
        result = {"Status" : "Error", "Message" : "File type not allowed"}
        return make_response(jsonify(result), 422)

    ic_number = request.form['ic']

    # Process request
    face_bbox, im = find_face(image)
    if len(face_bbox) != 4:
        result = {"Status" : "Error", "Message" : "No Face / More than one face detected"}
        return make_response(jsonify(result), 404)
    image = crop_face(im, face_bbox)
    
    # Check companies and ic exist
    companies_path = os.path.join('images',companies_id)
    check_folder(companies_path)
    ic_path = os.path.join(companies_path, ic_number)
    check_folder(ic_path)

    # Save image
    save_path = os.path.join(ic_path, '{}.jpg'.format(gen_uuid()))
    save_image(image, save_path)
    
    # Save Embedding
    emb = fr.face_encodings(image)
    append_one_embedding(ic_number, emb, initial)

    result = {"Status" : "Success", "Message" : "Identity successfully added"}
    return make_response(jsonify(result), 200)

@app.route('/predict', methods=['POST'])
@auth.login_required
def predict():
    username = g.user
    image = request.files['image']

    if allowed_file(secure_filename(image.filename)) is False:
        result = {"Status" : "Error", "Message" : "File type not allowed"}
        return make_response(jsonify(result), 422)

    # Process request
    face_bbox, im = find_face(image)
    if len(face_bbox) != 4:
        result = {"Status" : "Error", "Message" : "No Face / More than one face detected"}
        return make_response(jsonify(result), 404)
    image = crop_face(im, face_bbox)
    image = cv2.resize(image, (200, 200))

    # Save image
    save_path = os.path.join('images','raw', '{}.jpg'.format(gen_uuid()))
    check_folder(save_path)
    save_image(image, save_path)

    # Forward Pass Embedding
    emb = fr.face_encodings(image)[0]

    model, class_list = load_svm(username)

    best_class_prob, best_class_indices = predict_svm(model, emb)
    if best_class_prob > 0.4:
        result = {"Status" : "Success", "Identity" : class_list[best_class_indices]}
        return make_response(jsonify(result), 200)
    else:
        result = {"Status" : "Failed", "Identity" : "Unknown"}
        return make_response(jsonify(result), 404)


# Endpoint to train the svm
# Separate from adding new identity to due cpu intensive process
# Only trigger once all the identity are added

@app.route('/train', methods=['GET'])
@auth.login_required
def training():
    import time
    new_class_list = []
    class_list = get_list_ic()
    for cla in class_list:
        x = os.path.split(cla)
        new_class_list.append(x[-1])
    print("new class list", new_class_list)
    start_time = time.time()
    train_svm(new_class_list)
    result = {"Status" : "Success", "Message" : "Successfully Update Face Database", "Training Time": time.time() - start_time}
    return make_response(jsonify(result), 200)

@app.route('/initialize', methods=['GET'])
@basic_auth.login_required
def create():
    username = basic_auth.username()
    if username == "alphaadmin":
        create_encodings()
        result = {"Status" : "Success", "Message" : "Embeddings Initialized"}
        return make_response(jsonify(result), 200)
    else:
        result = {"Status" : "Failed", "Message" : "Unauthorized users"}
        return make_response(jsonify(result), 401)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)