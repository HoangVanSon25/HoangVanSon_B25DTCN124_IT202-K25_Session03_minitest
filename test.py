from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, timezone

app = FastAPI()


class Baseresponse(BaseModel):
    status_code: int
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str
    path: str


def create_response(req: Request, status_code: int, message: str, data: Optional[Any] = None, error: Optional[str] = None):
    return Baseresponse(
        status_code=status_code,
        message=message,
        data=data,
        error=error,
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=req.url.path
    ).model_dump()


class createFlightRequest(BaseModel):
    flight_number: str = Field(..., min_length=5, max_length=10)
    destination: str = Field(..., min_length=1)
    available_seats: int = Field(..., gt=0)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))


@app.exception_handler(HTTPException)
def http_exception_handler(req: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=create_response(
            req=req,
            status_code=exc.status_code,
            message=exc.detail,
            error=str(exc.detail)
        )
    )


flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45,
        "status": "scheduled", "created_at": "2026-07-01T06:00:00Z"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc",
        "available_seats": 12, "status": "scheduled", "created_at": "2026-07-01T07:30:00Z"}
]


@app.get("/flights")
def get_flights(req: Request, statuss: Optional[str] = None):
    filtered_flights = flights_db

    if statuss:
        filtered_flights = [
            flight for flight in flights_db if flight["status"].lower() == statuss.lower()
        ]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=create_response(
                req=req, status_code=200, message="successfully", data=filtered_flights)
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=create_response(req=req, status_code=200,
                                message="successfully", data=flights_db)
    )


@app.post("/flights")
def create_flight(req: Request, flight: createFlightRequest):
    new_id = max([f["id"] for f in flights_db], default=0) + 1

    flight_is_existing = next(
        (f for f in flights_db if f["flight_number"].upper(
        ) == flight.flight_number.upper()), None
    )

    if flight_is_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Mã chuyến bay trùng"
        )

    flight_data = flight.model_dump()
    flight_data["created_at"] = flight_data["created_at"].isoformat()

    new_flights = {"id": new_id, "status": "scheduled", **flight_data}
    flights_db.append(new_flights)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=create_response(
            req=req,
            status_code=201,
            message="Flight được tạo thành công",
            data=new_flights
        )
    )


@app.delete("/flights/{flight_id}")
def delete_flight(req: Request, flight_id: int):
    flight_to_delete = next(
        (f for f in flights_db if f["id"] == flight_id), None)

    if not flight_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chuyến bay với ID {flight_id} không tồn tại."
        )
    flights_db.remove(flight_to_delete)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=create_response(
            req=req,
            status_code=200,
            message="Xóa chuyến bay thành công",
            data=flight_to_delete
        )
    )
