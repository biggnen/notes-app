from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from pymongo import MongoClient
from passlib.context import CryptContext
from consul import Consul
import uuid
import httpx
from typing import List
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Union

app = FastAPI()


client = MongoClient("mongodb://mongodb:27017")
db = client["auth_db"]
users_collection = db["users"]


http_client = httpx.AsyncClient()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SECRET_KEY = "9e5daab1393a842a13d16a1ef93d637ffce69f3aef573d97bc59c0d42bbbf9f9"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    password: str


class UserInDB(User):
    hashed_password: str


class Document(BaseModel):
    title: str
    content: str
    topic_name: str = None


class DocumentUpdate(BaseModel):
    title: str
    content: str


class DocumentRelation(BaseModel):
    target_document_id: uuid.UUID
    relationship_type: str = "link"


class Attachment(BaseModel):
    filename: str
    file_type: str
    file_size: int


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


@app.post("/register")
async def register_user(user: User):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    new_user = {"username": user.username, "hashed_password": hashed_password}
    users_collection.insert_one(new_user)
    return {"message": "User registered successfully"}


@app.post("/token")
async def login_user(user: User):
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/apis")
async def list_apis(current_user: dict = Depends(get_current_user)):
    consul = Consul(host="consul", port=8500)
    services = consul.agent.services()
    api_services = {
        service: details["Address"]
        for service, details in services.items()
        if "api" in details["Tags"]
    }
    return api_services


@app.post("/documents")
async def create_document(
    doc: Document, current_user: dict = Depends(get_current_user)
):
    consul = Consul(host="consul", port=8500)
    services = consul.agent.services()
    notes_api_address = None
    for service, details in services.items():
        if service == "notes-api" and "api" in details["Tags"]:
            notes_api_address = f"http://{details['Address']}:{details['Port']}"
            break

    if not notes_api_address:
        raise HTTPException(status_code=500, detail="Notes API service not found")

    try:
        response = await http_client.post(
            f"{notes_api_address}/documents", json=doc.dict()
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail="Error creating document"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting to Notes API: {e}"
        )


@app.get("/documents/{document_id}")
async def get_document(
    document_id: uuid.UUID, current_user: dict = Depends(get_current_user)
):
    consul = Consul(host="consul", port=8500)
    services = consul.agent.services()
    notes_api_address = None
    for service, details in services.items():
        if service == "notes-api" and "api" in details["Tags"]:
            notes_api_address = f"http://{details['Address']}:{details['Port']}"
            break

    if not notes_api_address:
        raise HTTPException(status_code=500, detail="Notes API service not found")

    try:
        response = await http_client.get(f"{notes_api_address}/documents/{document_id}")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail="Error retrieving document"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting to Notes API: {e}"
        )


@app.put("/documents/{document_id}")
async def update_document(
    document_id: uuid.UUID,
    doc: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
):
    consul = Consul(host="consul", port=8500)
    services = consul.agent.services()
    notes_api_address = None
    for service, details in services.items():
        if service == "notes-api" and "api" in details["Tags"]:
            notes_api_address = f"http://{details['Address']}:{details['Port']}"
            break

    if not notes_api_address:
        raise HTTPException(status_code=500, detail="Notes API service not found")

    try:
        response = await http_client.put(
            f"{notes_api_address}/documents/{document_id}", json=doc.dict()
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail="Error updating document"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting to Notes API: {e}"
        )


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID, current_user: dict = Depends(get_current_user)
):
    consul = Consul(host="consul", port=8500)
    services = consul.agent.services()
    notes_api_address = None
    for service, details in services.items():
        if service == "notes-api" and "api" in details["Tags"]:
            notes_api_address = f"http://{details['Address']}:{details['Port']}"
            break

    if not notes_api_address:
        raise HTTPException(status_code=500, detail="Notes API service not found")

    try:
        response = await http_client.delete(
            f"{notes_api_address}/documents/{document_id}"
        )
        response.raise_for_status()
        return {"message": "Document deleted successfully"}
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail="Error deleting document"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, detail=f"Error connecting to Notes API: {e}"
        )


@app.get("/health")
async def health_check(current_user: dict = Depends(get_current_user)):
    return {"status": "ok"}
