from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    results = []

    if sort_col is search_sort_options.customer_name:
        order_by = db.carts.c.customer_name
    elif sort_col == search_sort_options.item_sku:
        order_by = db.potions.c.sku
    elif sort_col == search_sort_options.line_item_total:
        order_by = db.cart_items.c.quantity
    elif sort_col is search_sort_options.timestamp:
        order_by = db.cart_items.c.created_at
    else:
        assert False
         
    if sort_order == search_sort_order.asc:
        order_by = order_by.asc()
    else:
        order_by = order_by.desc()
    
    if(search_page == ""):
        search_page = 0
    else:
        search_page = int(search_page)
    
    stmt = (
        sqlalchemy.select(
            db.carts.c.customer_name.label("customer_name"),
            db.cart_items.c.cart_id.label("cart_id"),
            db.potions.c.sku.label("sku"),
            (db.cart_items.c.quantity * db.potions.c.price).label("total_price"),
            db.cart_items.c.created_at.label("created_at"),
            sqlalchemy.func.count().label("tot_results")
        )
        .select_from(db.cart_items
        .join(db.carts, db.carts.c.cart_id == db.cart_items.c.cart_id)
        .join(db.potions, db.potions.c.id == db.cart_items.c.potion_id)
        )
        .offset(search_page)
        .order_by(order_by)
    )
    
    if customer_name != "":
        stmt = stmt.where(db.carts.c.customer_name.ilike(f"%{customer_name}%"))
    
    if potion_sku != "":
        stmt = stmt.where(db.potions.c.sku.ilike(f"%{potion_sku}%"))

    results = []
    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        line_item_id = 0
        for row in result:
            if(line_item_id < 5):
                results.append(
                    {
                        "line_item_id": line_item_id,
                        "item_sku": row.sku,
                        "customer_name": row.customer_name,
                        "line_item_total": row.total_price,
                        "timestamp": row.created_at
                    }
                )
                line_item_id += 1
            
    prev = str(search_page - 5) if search_page - 5 >= 0 else ""
    next = str(search_page + 5) if search_page + 5 < result.first_row().tot_results else ""

    return {
        "previous": prev,
        "next": next,
        "results": results
    }

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
    with db.engine.begin() as connection:
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
                                           INSERT INTO potion_ledger (potion_change, potion_id)
                                           SELECT (cart_items.quantity * -1), cart_items.potion_id
                                           FROM cart_items
                                           WHERE cart_items.cart_id = :cart_id
                                           """),
                                        [{"cart_id": cart_id}])
        connection.execute(sqlalchemy.text("""
                                           INSERT INTO gold_ledger (gold_change) 
                                           VALUES (:gold_paid)
                                           """),
                                        [{"gold_paid": tot_gold}])

    
    return {"total_potions_bought": tot_pots, "total_gold_paid": tot_gold}
