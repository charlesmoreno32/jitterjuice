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
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + barrel.ml_per_barrel * barrel.quantity))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + barrel.price * barrel.quantity))
        elif(barrel.sku == "SMALL_GREEN_BARREL"):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + " + barrel.ml_per_barrel * barrel.quantity))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + barrel.price * barrel.quantity))
        elif(barrel.sku == "SMALL_BLUE_BARREL"):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + " + barrel.ml_per_barrel * barrel.quantity))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + barrel.price * barrel.quantity))
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    price = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
    first_row = result.first()

    curr_gold = first_row.gold
    num_red = 0
    num_green = 0
    num_blue = 0
    plan = []
    
    for barrel in wholesale_catalog:
        if(barrel.sku == "SMALL_RED_BARREL"):
            price = barrel.price
            break

    while(curr_gold > 0):
        for barrel in wholesale_catalog:
            if(barrel.sku == "SMALL_RED_BARREL" ):
                curr_gold -= barrel.price
                num_red += 1
                break
            elif(barrel.sku == "SMALL_GREEN_BARREL"):
                curr_gold -= barrel.price
                num_green += 1
                break
            elif(barrel.sku == "SMALL_BLUE_BARREL"):
                curr_gold -= barrel.price
                num_blue += 1
                break


    if(num_red > 0):
        plan.append(
            {
                "sku": "SMALL_RED_BARREL",
                "quantity": num_red,
            }
        )
    if(num_green > 0):
        plan.append(
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": num_green,
            }
        )
    if(num_blue > 0):
        plan.append(
            {
                "sku": "SMALL_BLUE_BARREL",
                "quantity": num_blue,
            }
        )
    
    return plan