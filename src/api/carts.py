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

@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts ()"))
    global cartid
    cartid += 1
    carts[cartid] = {}
    return {'cart_id': cartid}



@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart_id"), [{"cart_id": cart_id}])
    return cart


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart_id"), [{"cart_id": cart_id}])
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
    num_red = 0
    num_green = 0
    num_blue = 0
    for item_sku in cart:
        if(item_sku == "RED_POTION_0"):
            num_red += cart[item_sku]
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = num_red_potions - " + str(cart[item_sku])))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + " + str(num_red * 50)))
        elif(item_sku == "GREEN_POTION_0"):
            num_green+= cart[item_sku]
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions - " + str(cart[item_sku])))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + " + str(num_green * 50)))
        elif(item_sku == "BLUE_POTION_0"):
            num_blue += cart[item_sku]
            with db.engine.begin() as connection:
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = num_blue_potions - " + str(cart[item_sku])))
                connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + " + str(num_blue * 50)))
    tot_pots = num_red + num_green + num_blue
    return {"total_potions_bought": tot_pots, "total_gold_paid": tot_pots * 50}
