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
        result = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
    for row in result:
        quant = connection.execute(sqlalchemy.text("""SELECT SUM(potion_ledger.potion_change) as quant
                                                     FROM potions
                                                     JOIN potion_ledger ON potion_ledger.potion_id = potions.id
                                                     WHERE potions.potion_type = :potion_type
                                                     GROUP BY potions.id
                                                     """),
                                                     [{"potion_type": row.potion_type}]).scalar_one()
        if(quant > 0):
            catalog.append(
                {
                    "sku": row.sku,
                    "name": row.sku,
                    "quantity": row.inventory,
                    "price": row.price,
                    "potion_type": row.potion_type,
                }
            )

    return catalog