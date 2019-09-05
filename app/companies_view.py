from flask import Blueprint, Flask, jsonify, request, redirect, make_response, g

companies_api = Blueprint('companies_api', __name__)
from main_v2 import auth
from web_utils import *
from werkzeug import secure_filename

# Endpoint to list all companies

@companies_api.route('/companies', methods=['GET'])
# @swag_from(yaml.load(open("companies.yml")))
@auth.login_required
def get_companies():
    c_list, _ = get_list_companies()
    return make_response(jsonify({'companies_id':[int(i) for i in c_list]}), 200)

# Add company
# curl -H "Authorization: Bearer <Token>" "Content-Type: application/x-www-form-urlencoded" -d "company_id=5" http://127.0.0.1:5000/companies

@companies_api.route('/companies', methods=['POST'])
@auth.login_required
def post_companies():
    # Check companies and ic exist
    company_id = int(request.form['company_id'])
    company_path = os.path.join('images',str(company_id))
    status = check_folder(company_path)
    if status:
        return make_response(jsonify({"Status" : "Success", "Message" : "Company ID {} added to database".format(company_id)}), 200)
    else:
        return make_response(jsonify({"Status" : "Failed", "Message" : "Company ID {} already exist".format(company_id)}), 200)

# Delete company
# curl -H "Authorization: Bearer <Token>" "Content-Type: application/x-www-form-urlencoded" -d "company_id=5" http://127.0.0.1:5000/companies

@companies_api.route('/companies/<company_id>', methods=['DELETE'])
@auth.login_required
def delete_companies(company_id):
    # Check companies and ic exist
    force_delete = 'n'
    force_delete = request.form['force']
    c_list, base_url = get_list_companies()
    if str(company_id) not in c_list:
        result = {"Status" : "Error", "Message" : "Company ID not found"}
        return make_response(jsonify(result), 404)
    else:
        company_path = os.path.join('images',str(company_id))
    
    if not os.listdir(company_path):
        # is_empty = True
        os.remove(company_path)
        result = {"Status" : "Success", "Message" : "Company ID {} deleted".format(str(company_id))}
        return make_response(jsonify(result), 200)
    else:
        # is_empty = False
        if force_delete == 'y':
            import shutil
            shutil.rmtree(company_id)
            result = {"Status" : "Success", "Message" : "Company ID {} deleted".format(company_id)}
            return make_response(jsonify(result), 200)
        else:
            result = {"Status" : "Failed", "Message" : "Company ID {}'s folder is not empty, use force_delete with value of y".format(str(company_id))}
            return make_response(jsonify(result), 404)
    
# Endpoint to list ic in company
# Argument : company id

@companies_api.route('/companies/<company_id>/ic', methods=['GET'])
@auth.login_required
def get_ic(company_id):
    c_list, base_url = get_list_companies()
    
    if str(company_id) not in c_list:
        result = {"Status" : "Error", "Message" : "Company ID not found"}
        return make_response(jsonify(result), 404)
    else:
        ic_list = os.listdir(os.path.join(base_url,str(company_id)))
        return make_response(jsonify({'company_id':int(company_id), 'ic_list':ic_list}), 200)

# Endpoint to add image
# Arguments : image, ic
# Search face and save at ./companies/ic/uuid.jpg

@companies_api.route('/companies/<company_id>/ic', methods=['POST'])
@auth.login_required
def post_ic(company_id):        
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

    ic_number = request.form['ic_number']

    # Process request
    img = load_image_dlib(image)
    face_bbox, im, shape, im_large = find_face_dlib(img)

    # Legacy : face_recognition
    # face_bbox, im = find_face(image)

    if len(face_bbox) != 1:
        result = {"Status" : "Error", "Message" : "No Face / More than one face detected"}
        return make_response(jsonify(result), 404)

    # Legacy : face_recognition
    # image = crop_face(im, face_bbox)
    # image = cv2.resize(image, (250, 250))

    # Check companies and ic exist
    companies_path = os.path.join('images',company_id)
    check_folder(companies_path)
    ic_path = os.path.join(companies_path, ic_number)
    check_folder(ic_path)

    # Save image
    save_path = os.path.join(ic_path, '{}.jpg'.format(gen_uuid()))
    save_image(im_large, save_path)

    # Forward Pass Embedding
    emb = compute_emb(im, shape)
    append_one_embedding(ic_number, emb, initial)

    # Flip image
    img_flip = np.fliplr(img)
    face_bbox_flip, im_flip, shape_flip, im_flip_large = find_face_dlib(img_flip)

    if len(face_bbox_flip) != 1:
        result = {"Status" : "Error", "Message" : "No Face / More than one face detected"}
        return make_response(jsonify(result), 404)

    save_path = os.path.join(ic_path, '{}.jpg'.format(gen_uuid()))
    save_image(im_flip_large, save_path) 
    emb_flip = compute_emb(im_flip, shape_flip)
    append_one_embedding(ic_number, emb_flip, initial)

    result = {"Status" : "Success", "Message" : "Identity successfully added"}
    return make_response(jsonify(result), 200)


@companies_api.route('/companies/<company_id>/ic/<ic_number>', methods=['DELETE'])
@auth.login_required
def delete_ic(company_id, ic_number): 
    c_list, base_url = get_list_companies()

    if str(company_id) not in c_list:
        result = {"Status" : "Error", "Message" : "Company ID not found"}
        return make_response(jsonify(result), 404)
    else:
        ic_list = os.listdir(os.path.join(base_url,str(company_id)))
        if str(ic_number) not in ic_list:
            result = {"Status" : "Error", "Message" : "IC not found"}
            return make_response(jsonify(result), 404)
        else:
            import shutil
            shutil.rmtree(ic_list)
            result = {"Status" : "Success", "Message" : "IC number {} deleted from company ID {}".format(ic_number, company_id)}
            return make_response(jsonify(result), 200)

