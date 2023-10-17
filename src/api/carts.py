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
        id = connection.execute(sqlalchemy.text("""
                                                INSERT INTO carts (customer_name)
                                                VALUES (:customer_name)
                                                RETURNING cart_id
                                                """),
                                                [{"customer_name": new_cart.customer}]).scalar_one()
    return {'cart_id': id}



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
        connection.execute(sqlalchemy.text("""
                                           INSERT INTO cart_items (cart_id, quantity, potion_id) 
                                           SELECT :cart_id, :quantity, potions.id 
                                           FROM potions WHERE potions.sku = :item_sku
                                           """),
                                        [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    tot_pots = 0
    tot_gold = 0
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                           UPDATE potions
                                           SET inventory = potions.inventory - cart_items.quantity
                                           FROM cart_items
                                           WHERE potions.id = cart_items.potion_id and cart_items.cart_id = :cart_id;
                                           """ ), [{"cart_id": cart_id}])

        tot_pots = connection.execute(sqlalchemy.text("""
                                                      SELECT SUM(quantity) AS tot_pots
                                                      FROM cart_items
                                                      WHERE cart_id = :cart_id
                                                      """),
                                                      [{"cart_id": cart_id}]).scalar_one()
        tot_gold = connection.execute(sqlalchemy.text("""
                                                      SELECT SUM(quantity*price) AS tot_gold
                                                      FROM cart_items
                                                      JOIN potions ON potions.id = cart_items.potion_id
                                                      WHERE cart_id = :cart_id
                                                      """),
                                                      [{"cart_id": cart_id}]).scalar_one()
        connection.execute(sqlalchemy.text("""
                                           UPDATE globals
                                           SET gold = gold + :gold_paid
                                           """ ), [{"gold_paid": tot_gold}])

    
    return {"total_potions_bought": tot_pots, "total_gold_paid": tot_gold}
