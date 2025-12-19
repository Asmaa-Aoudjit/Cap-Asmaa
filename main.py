from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from math import radians, sin, cos, asin, sqrt

app = FastAPI(
    title="Campus Parking Finder",
    description="API to help CSCC students find the closest parking lot on Columbus Campus.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParkingLot(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    capacity: int
    occupied: int
    distance_m: Optional[float] = None 


#  Parking lots data
PARKING_LOTS = [
    {
        "id": 1,
        "name": "Lot A - Near Main Classroom",
        "latitude": 39.9680,
        "longitude": -82.9915,
        "capacity": 150,
        "occupied": 75,
    },
    {
        "id": 2,
        "name": "Lot B - Near Library",
        "latitude": 39.9670,
        "longitude": -82.9890,
        "capacity": 200,
        "occupied": 120,
    },
    {
        "id": 3,
        "name": "Lot C - Near Delaware Hall",
        "latitude": 39.9690,
        "longitude": -82.9930,
        "capacity": 180,
        "occupied": 90,
    },
    {
        "id": 4,
        "name": "Lot D - Remote Lot",
        "latitude": 39.9655,
        "longitude": -82.9875,
        "capacity": 250,
        "occupied": 40,
    },
]

#  In memory set of favorite parking lots
FAVORITES: set[int] = set()


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth in meters.
    """
    R = 6371_000  # radius of Earth in meters
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


@app.get("/api/parking-lots", response_model=List[ParkingLot])
def list_parking_lots(lat: float | None = None, lon: float | None = None):
    """
    List all parking lots.
    If lat/lon are provided including distance and sort by closest.
    """
    lots: List[ParkingLot] = []

    for lot in PARKING_LOTS:
        lot_model = ParkingLot(**lot)
        if lat is not None and lon is not None:
            lot_model.distance_m = haversine_distance_m(
                lat, lon, lot_model.latitude, lot_model.longitude
            )
        lots.append(lot_model)

    if lat is not None and lon is not None:
        lots.sort(key=lambda l: l.distance_m or 0)

    return lots


@app.get("/api/closest", response_model=ParkingLot)
def get_closest_lot(lat: float, lon: float):
    """
    Return the single closest parking lot to the given coordinates.
    """
    lots_with_distance: List[ParkingLot] = []

    for lot in PARKING_LOTS:
        lot_model = ParkingLot(**lot)
        lot_model.distance_m = haversine_distance_m(
            lat, lon, lot_model.latitude, lot_model.longitude
        )
        lots_with_distance.append(lot_model)

    if not lots_with_distance:
        raise HTTPException(status_code=404, detail="No parking lots defined")

    closest = min(lots_with_distance, key=lambda l: l.distance_m or 0)
    return closest


@app.get("/api/favorites", response_model=List[ParkingLot])
def get_favorites():
    """
    Get all favorite parking lots.
    """
    favorite_lots = [ParkingLot(**lot) for lot in PARKING_LOTS if lot["id"] in FAVORITES]
    return favorite_lots




@app.post("/api/favorites/{lot_id}", response_model=ParkingLot)
def add_favorite(lot_id: int):
    """
    Add a parking lot to favorites.
    """
    lot = next((lot for lot in PARKING_LOTS if lot["id"] == lot_id), None)
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    FAVORITES.add(lot_id)
    return ParkingLot(**lot)



@app.delete("/api/favorites/{lot_id}")
def remove_favorite(lot_id: int):
    """
    Remove a parking lot from favorites.
    """
    if lot_id in FAVORITES:
        FAVORITES.remove(lot_id)
    return {"status": "ok", "removed": lot_id}


@app.get("/")
def root():
    return {"message": "Campus Parking Finder API is running. Frontend calls /api/* endpoints."}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
