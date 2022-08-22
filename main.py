
from square.client import Client
import os
import uuid
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException, Form, UploadFile
from sqlalchemy.orm import Session
from PIL import Image as PIL_Image
import crud, models, schemas
from database import SessionLocal, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv
load_dotenv() 

models.Base.metadata.create_all(bind=engine)

from utils import create_checkout_link, create_reciept, obtain_oauth

app = FastAPI()
origins = [
    "https://tickup.netlify.app/",
    "http://localhost:3000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = os.environ['OWN_BASE_URL']

print(BASE_URL)
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/api/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/api/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/api/users/{user_id}/items/", response_model=schemas.Item )
def create_item_for_user(
    user_id: int,
    file: UploadFile,
    title:str = Form(...), 
    description: str = Form(...), 
    price:int = Form(...),
    total_seats:int = Form(...),
    departure_date:str = Form('31-12-2022T23:59'),
    days:int = Form(3),
    db: Session = Depends(get_db)
):
    print(file, file.filename)
    try:
        im = PIL_Image.open(file.file)
    except Exception:
        raise HTTPException(status_code=400, detail="Image Error")
    db_user = crud.get_user(db=db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    item =  schemas.ItemCreate(
        title=title,
        description=description,
        stock= total_seats,
        total_seats=total_seats,
        price=price,
        image=file.filename,
        departure_date=departure_date,
        days=days,
        state='Scheduled'
    )
    item = crud.create_user_item(db=db, item=item, user_id=user_id)
    im.save(f'images/{item.id}-{file.filename}')
    return item


@app.get("/api/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items

@app.get("/api/items/{item_id}", response_model=schemas.Item)
def read_items(item_id:int, db: Session = Depends(get_db)):
    items = crud.get_item(db, item_id = item_id)
    return items


@app.get('/api/create_checkout')
def create_checkout(item_id:int, quantity:int, db: Session = Depends(get_db)):
    if quantity<1:
        raise HTTPException(status_code=400, detail="quantity cant be less than 1")
    
    db_item = crud.get_item(db=db, item_id=item_id)
    if not db_item:
        raise HTTPException(status_code=400, detail="item not found")
    
    if db_item.stock < quantity:
        raise HTTPException(status_code=400, detail="not enough items left. try fewer quantity")
    db_user = crud.get_user(db=db, user_id=db_item.owner_id)
    if not db_user:
        raise HTTPException(status_code=400, detail="ticket owner doesnt exist anymore")
        
    result =  create_checkout_link(db_user.access_key, db_user.location_id, db_item.title, str(quantity), db_item.price, redirect_url=os.environ["OWN_BASE_URL"]+'ticket-bought',currency=db_user.currency,)
    print(item_id)
    if result.is_success():
        #save transaction
        db_checkout = crud.create_checkout(
            db=db, 
            item_id=item_id, 
            quantity=quantity, 
            checkout_id=result.body['checkout']['id'],
            checkout_total=result.body['checkout']['order']['net_amount_due_money']['amount'],
            checkout_url=result.body['checkout']['checkout_page_url']
        )
        return {'status':'success', 'checkout_url':result.body['checkout']['checkout_page_url']}
    elif result.is_error():
        print(result.errors)
        return HTTPException(status_code=400, detail=result.errors)


@app.get('/api/ticket-bought', response_class=HTMLResponse)
def ticket_bought(checkoutId:str, transactionId:str, db: Session = Depends(get_db) ):
    print(checkoutId, transactionId)

    db_checkout = db.query(models.Checkout).filter(models.Checkout.checkout_id == checkoutId).first()
    if not db_checkout:
        raise HTTPException(status_code=400, detail="Checkout not found")

    #decrease available stock    
    itemid = db_checkout.item_id
    quantity = db_checkout.quantity
    db_item = crud.get_item(db=db, item_id=itemid)
    old_stock = db_item.stock
    new_stock = old_stock - quantity
    if new_stock <=0:
        new_stock = 0
    
    db_item.stock = new_stock
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    #save transaction id so we can verify it later
    db_checkout.transaction_id = transactionId
    db.add(db_checkout)
    db.commit()
    db.refresh(db_checkout)


    db_seller = db.query(models.User).filter(models.User.id == db_item.owner_id).first()
    if not db_seller:
        raise HTTPException(status_code=400, detail="Seller not found")


    #create pdf receipt
    create_reciept(
        checkout=db_checkout, item=db_item, seller=db_seller
    )



    html_content = f"""
    <html>
        <head>
            <title>Some HTML in here</title>
        </head>
        <body style="height:100%;display:flex; justify-content:center; align-item:center;">
            <div>
                <h1 style="text-align:center;" >Redirecting...</h1>
                <a hidden download href='/api/pdf/{checkoutId}' >Download Receipt</a>
            </div>
            <script>
                document.querySelector('a').click()
                location='{os.environ['OWN_FRONTEND_URL']}ticket-bought/'
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.get('/api/pdf/{checkoutId}',  response_class=FileResponse)
def get_pdf(checkoutId:str,):
    path = f'receipts/{checkoutId}.pdf'
    if os.path.exists(path):
        return path
    else:
        raise HTTPException(status_code=404, detail='Receipt Not Found') 
    
    


@app.get('/api/oauth-redirect')
def redirect(code:str, response_type:str, state:str, db: Session = Depends(get_db)):
    result = obtain_oauth(
        os.environ['OWN_ACCESS_TOKEN'], 
        own_client_id=os.environ['OWN_CLIENT_ID'], 
        own_secret=os.environ['OWN_SECRET'],
        code=code
        )
    access_token = result.body['access_token']
    merchant_id = result.body['merchant_id']
    client = Client(
        access_token=result.body['access_token'],
        environment='production'
        )
    loc_result = client.locations.list_locations()

    if loc_result.is_success():
        print(loc_result.body)
        location_id = loc_result.body['locations'][0]['id']
        name = loc_result.body['locations'][0]['name']
        currency = loc_result.body['locations'][0]['currency']

        db_user = models.User(name=name, merchant_id=merchant_id, location_id=location_id, currency=currency, access_key=access_token)
        db.add(db_user)
        db.commit()
        
        db.refresh(db_user)
        return db_user

    elif loc_result.is_error():
        print(loc_result.errors)

    if result.is_success():
        print(result.body)
        return result
    elif result.is_error():
        return result.errors
        # print(result.errors)
    return 'authe success'

@app.get('/api/oauth-link')
def oauth_link():
    return f'https://squareup.com/oauth2/authorize?client_id=sq0idp-FuPiCIjGxeZe7JmFVfq68w&scope=PAYMENTS_WRITE+ORDERS_WRITE+ORDERS_READ+MERCHANT_PROFILE_READ&state=82201dd8d83d23cc8a48caf52b'

app.mount("/api/images", StaticFiles(directory="images"), name="static_images")