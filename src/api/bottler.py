from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    for potion in potions_delivered:
        if((potion.potion_type)[0] == 100):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_red_ml - " + str(potion.quantity * 100)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions + " + str(potion.quantity)))
        if((potion.potion_type)[1] == 100):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml - " + str(potion.quantity * 100)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + " + str(potion.quantity)))
        if((potion.potion_type)[2] == 100):
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_blue_ml - " + str(potion.quantity * 100)))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions + " + str(potion.quantity)))
    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml FROM global_inventory"))
    first_row = result.first()
    plan = []
    num_red = int(first_row.num_red_ml / 100)
    num_green = int(first_row.num_green_ml / 100)
    num_blue = int(first_row.num_blue_ml / 100)
    
    if(num_red > 0):
        plan.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": num_red,
            }
        )
    if(num_green > 0):
        plan.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": num_green,
            }
        )
    if(num_blue > 0):
        plan.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": num_blue,
            }
        )
   
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    return plan
