from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        globals = connection.execute(sqlalchemy.text("SELECT * FROM globals"))
        catalog = connection.execute(sqlalchemy.text("SELECT inventory FROM catalog"))

    first_row = globals.first()
    tot_pots = 0
    tot_ml = first_row.num_red_ml + first_row.num_green_ml + first_row.num_blue_ml + first_row.num_dark_ml
    for row in catalog:
        tot_pots += row.inventory    
    return {"number_of_potions": tot_pots, "ml_in_barrels": tot_ml, "gold": first_row.gold}

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
