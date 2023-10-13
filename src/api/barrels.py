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
    gold_paid = 0
    red_ml = 0
    green_ml = 0
    blue_ml = 0
    dark_ml = 0
    for barrel in barrels_delivered:
        gold_paid += barrel.price + barrel.quantity
        if(barrel.potion_type == [1,0,0,0]):
            red_ml += barrel.ml_per_barrel * barrel.quantity
        elif(barrel.potion_type == [0,1,0,0]):
            green_ml += barrel.ml_per_barrel * barrel.quantity
        elif(barrel.potion_type == [0,0,1,0]):
            blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif(barrel.potion_type == [0,0,0,1]):
            dark_ml += barrel.ml_per_barrel * barrel.quantity
        else:
            raise Exception('Invalid potion type')
    
    print(f"gold paid: {gold_paid} red_ml: {red_ml} blue_ml: {blue_ml} green_ml: {green_ml} dark_ml: {dark_ml}")
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE globals SET
                red_ml = red_ml + :red_ml,
                green_ml = green_ml + :green_ml,
                blue_ml = blue_ml + :blue_ml,
                dark_ml = dark_ml + :dark_ml,
                gold = gold - :gold_paid
                """),
            [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml, "gold_paid": gold_paid}]
        )
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    price = 0
    with db.engine.begin() as connection:
        globals = connection.execute(sqlalchemy.text("SELECT gold FROM globals"))
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions"))

    first_row = globals.first()

    curr_gold = first_row.gold
    plan = []
    times = 0

    
    #while(curr_gold > 0 and times < 999):
        #times += 1
    for barrel in wholesale_catalog:
        quan = 0
        if(curr_gold >= barrel.price):
            if('SMALL' in barrel.sku):
                    curr_gold -= barrel.price
                    barrel.quantity -= 1
                    plan.append(
                         {
                              "sku": barrel.sku,
                              "quantity": 1
                         }
                    )
    
    return plan