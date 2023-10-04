from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    for barrel in barrels_delivered:
        if(barrel.sku == "SMALL_RED_BARREL"):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + barrel.ml_per_barrel))
            with db.engine.begin() as connection:    
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + barrel.price))

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    price = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, gold FROM global_inventory"))
    first_row = result.first()
    for barrel in wholesale_catalog:
        if(barrel.sku == "SMALL_RED_BARREL"):
            price = barrel.price
            break

    if(first_row.num_red_potions < 10 and first_row.gold > price):
        quantity = 1
    else:
        return []
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": quantity,
        }
    ]
