from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel

DATABASE_NAME = "hotel"
COLLECTION_NAME = "reservation"
MONGO_DB_URL = "mongodb://localhost"
MONGO_DB_PORT = 27017


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(f"{MONGO_DB_URL}:{MONGO_DB_PORT}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()

def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name:str):
    result=[]
    for i in collection.find({"name":name},{"_id":0}):
        result.append(i)
    return {"result":result}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    result=[]
    for i in collection.find({"room_id":room_id},{"_id":0}):
        result.append(i)
    return {"result":result}

@app.post("/reservation")
def reserve(reservation : Reservation):
    reservation.start_date=reservation.start_date.isoformat()
    reservation.end_date=reservation.end_date.isoformat()
    if (reservation.start_date > reservation.end_date) or reservation.room_id<1 or reservation.room_id>10:
        raise HTTPException(status_code=400)
    if room_avaliable(reservation.room_id,str(reservation.start_date),str(reservation.end_date)):
        collection.insert_one({"name":reservation.name,"start_date":str(reservation.start_date),"end_date":str(reservation.end_date),"room_id":reservation.room_id})
    else:
        raise HTTPException(status_code=400)
    return

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    print(type(reservation.start_date))
    new_start_date=new_start_date.isoformat()
    new_end_date=new_end_date.isoformat()
    if(new_end_date<new_start_date) or reservation.room_id>10 or reservation.room_id<1:
        raise HTTPException(status_code=400)
    elif(room_avaliable(reservation.room_id,str(new_start_date),str(new_end_date))):
        collection.update_many({"name":reservation.name,"start_date":str(reservation.start_date),"end_date":str(reservation.end_date),"room_id":reservation.room_id},{"$set": {"name":reservation.name,"start_date":str(new_start_date),"end_date":str(new_end_date),"room_id":reservation.room_id}})
    else:
        raise HTTPException(status_code=400)
    return
@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    reservation.start_date=reservation.start_date.isoformat()
    reservation.end_date=reservation.end_date.isoformat()
    collection.delete_many({"name":reservation.name,"start_date":str(reservation.start_date),"end_date":str(reservation.end_date),"room_id":reservation.room_id})