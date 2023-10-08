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
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml + " + str(barrel.ml_per_barrel * barrel.quantity)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(barrel.price * barrel.quantity)))
        elif((barrel.potion_type)[1] == 100):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + " + str(barrel.ml_per_barrel * barrel.quantity)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(barrel.price * barrel.quantity)))
        elif((barrel.potion_type)[2] == 100):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml + " + str(barrel.ml_per_barrel * barrel.quantity)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - " + str(barrel.price * barrel.quantity)))
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    price = 0
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    first_row = result.first()

    curr_gold = first_row.gold
    num_red = 0
    num_green = 0
    num_blue = 0
    plan = []
    times = 0


    while(curr_gold > 0 and times < 10):
        times += 1
        for barrel in wholesale_catalog:
            if(curr_gold >= barrel.price):
                if(barrel.sku == "SMALL_RED_BARREL" and barrel.quantity > 0 and (first_row.num_red_potions == 0 or first_row.num_red_potions < (first_row.num_green_potions)*2 and first_row.num_red_potions < (first_row.num_blue_potions)*2)):
                    curr_gold -= barrel.price
                    num_red += 1
                    barrel.quantity -= 1
                elif((barrel.potion_type)[1] == 100 and barrel.quantity > 0 and (first_row.num_green_potions == 0 or first_row.num_green_potions < (first_row.num_red_potions)*2 and first_row.num_green_potions < (first_row.num_blue_potions)*2)):
                    curr_gold -= barrel.price
                    num_green += 1
                    barrel.quantity -= 1
                elif((barrel.potion_type)[2] == 100 and barrel.quantity > 0 and (first_row.num_blue_potions == 0 or first_row.num_blue_potions < (first_row.num_red_potions)*2 and first_row.num_blue_potions < (first_row.num_green_potions)*2)):
                    curr_gold -= barrel.price
                    num_blue += 1
                    barrel.quantity -= 1

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