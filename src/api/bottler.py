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
    print(potions_delivered)
    with db.engine.begin() as connection:
        tot_pots = sum(potion.quantity for potion in potions_delivered)
        red_ml = sum(potion.quantity * potion.potion_type[0] for potion in potions_delivered)
        green_ml = sum(potion.quantity * potion.potion_type[1] for potion in potions_delivered)
        blue_ml = sum(potion.quantity * potion.potion_type[2] for potion in potions_delivered)
        dark_ml = sum(potion.quantity * potion.potion_type[3] for potion in potions_delivered)

        for potion in potions_delivered:
            connection.execute(
                sqlalchemy.text("""
                                UPDATE potions
                                SET inventory = inventory + :new_pots
                                WHERE type = :potion_type
                                """),
                [{"tot_pots": potion.quantity, "potion_type": potion.potion_type}]
            )
        connection.execute(
            sqlalchemy.text("""
                            UPDATE globals SET
                            red_ml = red_ml + :red_ml,
                            green_ml = green_ml + :green_ml,
                            blue_ml = blue_ml + :blue_ml,
                            dark_ml = dark_ml + :dark_ml
                            """),
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}]
        )

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM global_inventory"))
    first_row = result.first()
    plan = []
    num_red = int(first_row.red_ml / 100)
    num_green = int(first_row.green_ml / 100)
    num_blue = int(first_row.blue_ml / 100)
    num_dark = int(first_row.dark_ml / 100)
    
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
