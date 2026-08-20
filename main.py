from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from src.exceptions import ContactNotFoundError, ContactAlreadyExistsError
from src.routes import contacts, auth
from src.limiter import limiter

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')

@app.get('/')
def greeting():

    return {'message': 'Hello Guest!'}

@app.exception_handler(ContactNotFoundError)
async def contact_not_found_handler(request: Request, exc: ContactNotFoundError):

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'detail': exc.message}
    )

@app.exception_handler(ContactAlreadyExistsError)
async def contact_already_exist_handler(request: Request, exc: ContactAlreadyExistsError):

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': 'Contact already exist'}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=jsonable_encoder({'detail': exc.errors()})
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'detail': 'Internal sever error'}
    )