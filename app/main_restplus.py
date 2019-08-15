'''
# GET /companies/
    - list all companies

# POST /companies/
    - Create new company

# DELETE /companies/{company_id}
    - Delete a company by company_id

# GET /companies/{company_id}
    - Get list of ic in company

# GET /companies/{company_id}/ic/
    - Get list of ic in company

# POST /companies/{company_id}/ic/{ic_number}/
    - Add new ic to company

# DELETE /companies/{company_id}/ic/{ic_number}/
    - Delete ic in company_id
'''

from flask import Flask
from flask_restplus import Api, Resource, fields
from web_utils import *

app = Flask(__name__)
api = Api(app)

company_model = api.model('List of Companies', {'company_id' : fields.Integer('Company ID')})
ic_list = api.model('IC List', {
    'ic': fields.String('IC number')
})
company_ic_model = api.model('List of ICs', {
    'company_id': fields.Integer(required=True, description='Company ID'),
    'ic_list': fields.Nested(ic_list, description='List of IC in the company')
})

@api.route('/companies')
class Companies(Resource):
    @api.marshal_with(company_model, envelope='list_of_companies', mask=None)
    def get(self):
        c_list, _ = get_list_companies()
        return [{'company_id': int(c)} for c in c_list], 200
        # return c_list, 200
'''
    def post(self):
'''
@api.route('/companies/<int:company_id>')
class ListCompanies(Resource):
    # def delete(self):
    @api.marshal_list_with(company_ic_model, mask=None)
    def get(self, company_id):
        c_list, base_url = get_list_companies()
        ic_list = os.listdir(os.path.join(base_url, str(company_id)))

        if str(company_id) in c_list:
            return {'company_id':company_id, 'ic_list':[{'ic': ic } for ic in ic_list]}, 200
'''
@api.route('/companies/<int:company_id>/ic')
class IC(Resource):
    def get(self):

@api.route('/companies/<int:company_id>/ic/<int:ic_number')
class ListIC(Resource):
    def get(self):
'''
if __name__ == '__main__':
    app.run(debug=True)
