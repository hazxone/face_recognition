import pickle
import os
import cv2
import time
import uuid
import numpy as np
import face_recognition as fr
from sklearn.svm import SVC
from sklearn.externals import joblib
from face_recognition.face_recognition_cli import image_files_in_folder

pickle_name = "blank.p"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Pickle file list
# |- session.token : Latest token string
# |- users.cred : Username basicauth
# |- X_y.npz : face and ic embeddings
# |- {company}_svm.embeddings : Trained SVM

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

def check_folder(folder_path):
    """Check if folder exist, if not create directory
    
    Arguments:
        folder_path {str} -- Path to folder
    """
    created = False
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        created = True
        return created
    else:
        return created

def find_face(img):
    im = fr.load_image_file(img)
    return fr.face_locations(im, number_of_times_to_upsample=2)[0], im

def crop_face(im, face_bbox):
    im_height, im_width, _ = im.shape
    top, right, bottom, left = face_bbox
    height = abs(top - bottom)
    pad = int(0.1 * height)
    if left - pad < 0:
        left = left
    else:
        left = left - pad

    if right + pad > im_width:
        right = im_width
    else:
        right = right + pad

    if top - pad < 0:
        top = 0
    else:
        top = top - pad

    if bottom + pad > im_height:
        bottom = im_height
    else:
        bottom = bottom + pad

    crop = im[top:bottom, left:right]
    return crop

def save_image(img, save_path):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # img_rgb = cv2.resize(img_rgb, (250, 250))
    cv2.imwrite(save_path, img_rgb)

def gen_uuid():
    return uuid.uuid4().hex 

def save_pickle(filename, extension, new_dict):
    pickle_name = os.path.join('pickle','{}.{}'.format(filename, extension))
    with open(pickle_name, 'wb') as f:
        pickle.dump(new_dict, f)

def get_list_ic():
    base_path = 'images'
    ic_paths = []
    c_list = os.listdir(base_path)
    for c in c_list:
        ic_list = os.listdir(os.path.join(base_path, c))
        add_path = os.path.join(base_path, c)
        ic_list = [os.path.join(add_path, s) for s in ic_list]
        ic_paths.extend(ic_list)
    return ic_paths

def get_list_companies():
    base_path = 'images'
    return os.listdir(base_path), base_path

#@admin only - Generate all encodings
def create_encodings():
    stime = time.time()
    X = []
    y = []
    companies_list, base_path = get_list_companies()
    for company in companies_list:
        ic_list = os.listdir(os.path.join(base_path,company))
        for ic in ic_list:
            for img_path in image_files_in_folder(os.path.join(base_path, company, ic)):
                image = fr.load_image_file(img_path)
                face_bounding_boxes = fr.face_locations(image)

                if len(face_bounding_boxes) != 1:
                    # If there are no people (or too many people) in a training image, skip the image.
                    print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(face_bounding_boxes) < 1 else "Found more than one face"))
                else:
                    # Add face encoding for current image to the training set
                    X.append(fr.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
                    y.append(ic)
                    print(img_path, ic)

    X = np.asarray(X)
    print("this", X.shape)
    print("this y", y)
    y = np.asarray(y)
    np.savez(os.path.join('pickle','X_y'), X=X, y=y)
    print(time.time() - stime)

def append_one_embedding(ic, emb, initial=False):
    if initial:
        create_encodings()
    else:
        X_old, y_old = load_numpy_compressed()
        print("Xold", X_old.shape)
        emb = np.asarray(emb)
        print("emb", emb.shape)
        X = np.concatenate((X_old, emb.reshape(1,-1)), axis=0)
        y = np.append(y_old, ic)
        np.savez(os.path.join('pickle','X_y'), X=X, y=y)

def load_numpy_compressed():
    # Find npz, if not return error
    if os.path.isfile(os.path.join('pickle','X_y.npz')):
        load_npz = np.load(os.path.join('pickle','X_y.npz'))
        X = load_npz['X']
        y = load_npz['y']
        return X, y
    else:
        print("File not found")

def train_svm(class_list):
    X, y = load_numpy_compressed()
    print("shape x ", X.shape)
    print("shape y ", y.shape)
    # svm_object = SVC(kernel='linear', probability=True)
    svm_object = SVC(kernel='linear', probability=True)
    svm_object.fit(X, y)
    save_pickle('medkad_svm', 'embeddings', (svm_object, class_list))

def load_svm(username):
    with open(os.path.join('pickle','{}_svm.embeddings'.format(username)), 'rb') as infile:
        (model, class_names) = joblib.load(infile)
        print("Class name", class_names)
    return model, class_names

def predict_svm(model, unknown_encoding):
    # (1,-1) reshape to row 1 unknown column to fit the original data
    prediction = model.predict_proba(unknown_encoding.reshape(1,-1))
    best_class_indices = np.argmax(prediction, axis=1)
    best_class_probabilities = prediction[np.arange(len(best_class_indices)), best_class_indices]
    print(prediction[0], best_class_indices, best_class_probabilities)
    return best_class_probabilities[0], best_class_indices[0]






# def create_encodings():
#     stime = time.time()
#     X = []
#     y = []
#     ic_paths = get_list_ic()
#     for ic in ic_paths:
#         for img_path in image_files_in_folder(ic):
#             path, class_dir = os.path.split(ic)
#             image = fr.load_image_file(img_path)
#             face_bounding_boxes = fr.face_locations(image)

#             if len(face_bounding_boxes) != 1:
#                 # If there are no people (or too many people) in a training image, skip the image.
#                 if verbose:
#                     print("Image {} not suitable for training: {}".format(img_path, "Didn't find a face" if len(face_bounding_boxes) < 1 else "Found more than one face"))
#             else:
#                 # Add face encoding for current image to the training set
#                 X.append(fr.face_encodings(image, known_face_locations=face_bounding_boxes)[0])
#                 y.append(class_dir)
#     print("Enc",X)
#     print("class", y)
#     print(time.time() - stime)
