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
    customer_name = "" + str(cartid)
    carts[cartid] = {}
    with db.engine.begin() as connection:
        id = connection.execute(sqlalchemy.text("""
                                                INSERT INTO carts (customer_name)
                                                VALUES (:customer_name)
                                                RETURNING id
                                                """),
                                                [{"customer_name": customer_name}])
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
        cart = connection.execute(sqlalchemy.text(""""
                                                  INSERT INTO cart_items (cart_id, quantity, potion_id) 
                                                  SELECT :cart_id, :quantity, potion.id 
                                                  FROM potions WHERE potion.sku = :item_sku
                                                  """),
                                                [{"cart_id": cart_id, "quantity": cart_item.quantity, "item_sku": item_sku}])
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global carts
    cart = carts[cart_id]
    tot_pots = 0
    tot_gold = 0
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart_id"), [{"cart_id": cart_id}])
        start = cart
        for item in cart:
            tot_pots += item.quantity
            connection.execute(sqlalchemy.text("""
                                               UPDATE potions
                                               SET inventory = potions.inventory - cart_items.quantity
                                               FROM cart_items
                                               WHERE potions.id = cart_items.potion_id and cart_items.cart_id = :cart_id;
                                               """ ), [{"cart_id": item.cart_id}])
            #somehow do the gold transaction
            connection.execute(sqlalchemy.text( """
                                                UPDATE globals
                                                SET gold = gold - :tot_price
                                                """),
                                                [{"tot_price": item.quantity * 50}])
        """connection.execute(sqlalchemy.text(""
                                           DELETE FROM cart_items
                                           WHERE cart_id = :cart_id
                                           ""),
                                           [{"cart_id": cart_id}])"""
        connection.execute(sqlalchemy.text("""
                                           DELETE FROM carts
                                           WHERE cart_id = :cart_id
                                           """),
                                           [{"cart_id": cart_id}])
    
    return {"total_potions_bought": tot_pots, "total_gold_paid": tot_pots * 50}
