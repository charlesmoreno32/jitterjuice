from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    # Can return a max of 20 items.

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_potions, num_green_potions, num_blue_potions FROM global_inventory"))
    first_row = result.first()

    return [
            {
                "sku": "RED_POTION_0",
                "name": "red potion",
                "quantity": first_row.num_red_potions,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            },
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": first_row.num_green_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            },
            {
                "sku": "BLUE_POTION_0",
                "name": "blue potion",
                "quantity": first_row.num_blue_potions,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }
        ]
