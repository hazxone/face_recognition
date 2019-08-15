from fastapi import FastAPI
from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse

API_KEY = "123456789"
API_KEY_NAME = "api_token"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
):

    if api_key_query == API_KEY:
        return api_key_query
    elif api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


# Get list of employees
# /users/companies/ic-number

@app.get("/companies", tags=["companies"])
async def get_open_api_endpoint(api_key: APIKey = Depends(get_api_key)):
    response = "How cool is this?"
    return response

'''
@app.get('/companies')
async def list_companies():
    return list of companies

@app.get('/companies/{company_id}')
async def get_company(company_id):
    return all users in that company

# Create register user endpoint
@app.post('/companies/{company_id}')
async def register_user():
    # add user to the company
    # crop face
    # save image in data/ic/uuid.jpg

'''