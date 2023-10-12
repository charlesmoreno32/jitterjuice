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
    catalog = []

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM globals"))
    for row in result:
        if(row.inventory > 0):
            catalog.append(
                {
                    "sku": result.sku,
                    "name": result.sku,
                    "quantity": result.inventory,
                    "price": result.price,
                    "potion_type": [row.red, row.green, row.blue, row.dark],
                }
        )

    return catalog