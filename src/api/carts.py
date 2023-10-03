from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


carts = {}
cartid = 0
@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    global cartid
    cartid += 1
    carts[cartid] = {}
    return {'cart_id': cartid}



@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    global carts
    return {carts[cart_id]}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global carts
    cart = carts[cart_id]
    cart[item_sku] = cart_item.quantity

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global carts
    cart = carts[cart_id]
    tot_pots = 0
    for item_sku in cart:
        if(item_sku == "RED_POTION_0"):
            tot_pots += cart[item_sku]
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions - " + cart[item_sku]))
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + " + tot_pots * 50))

    return {"total_potions_bought": tot_pots, "total_gold_paid": tot_pots * 50}
