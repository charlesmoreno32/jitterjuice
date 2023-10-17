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
                                WHERE potion_type = :potion_type
                                """),
                [{"new_pots": potion.quantity, "potion_type": potion.potion_type}]
            )
        connection.execute(
            sqlalchemy.text("""
                            UPDATE globals SET
                            red_ml = red_ml - :red_ml,
                            green_ml = green_ml - :green_ml,
                            blue_ml = blue_ml - :blue_ml,
                            dark_ml = dark_ml - :dark_ml
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
    #TOT POTS HAS TO BE <= 300
    #to get potion id: 
    #SELECT id FROM potions WHERE sku = :item_sku
    #INSERT INTO cart items (cart_id, quantity, potion_id)
    #VALUES( :cart_id, :quantity, :catalog_id)


    #INSERT INTO cart_items (cart_id, quantity, catalog_id)
    #SELECT :cart_id, :quantity, potions.id
    #FROM potions WHERE potions.sku = :item_sku
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM globals"))
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
    potion_lst = [pot for pot in potions]
    inventory = 0
    gl = result.first()
    plan = []
    quants = {}
    red_ml = gl.red_ml
    green_ml = gl.green_ml
    blue_ml = gl.blue_ml
    dark_ml = gl.dark_ml
    count = 0

    for potion in potion_lst:
        count += 1
        inventory += potion.inventory
        quants[potion.sku] = 0
    times = 0
    while(inventory < 300 and times < count):
        times = 0
        for potion in potion_lst:
            if(inventory < 300 and potion.potion_type[0] <= red_ml and potion.potion_type[1] <= green_ml and potion.potion_type[2] <= blue_ml and potion.potion_type[3] <= dark_ml):
                red_ml -= potion.potion_type[0]
                green_ml -= potion.potion_type[1]
                blue_ml -= potion.potion_type[2]
                dark_ml -= potion.potion_type[3]
                quants[potion.sku] += 1
                inventory += 1
            else:
                times += 1

    for potion in potion_lst:
        if(quants[potion.sku] != 0):
            plan.append(
                {
                    "potion_type": potion.potion_type,
                    "quantity": quants[potion.sku],
                }
            )
    
    """plan = [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": 5,
            }
            ]"""
    return plan