from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# -----------------------------
# Q1 - HOME ROUTE
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Food Delivery"}

# -----------------------------
# DATA
# -----------------------------
menu = [
    {"id": 1, "name": "Margherita Pizza", "price": 200, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Veg Burger", "price": 120, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Coke", "price": 50, "category": "Drink", "is_available": True},
    {"id": 4, "name": "Chocolate Cake", "price": 150, "category": "Dessert", "is_available": False},
    {"id": 5, "name": "Paneer Pizza", "price": 250, "category": "Pizza", "is_available": True},
    {"id": 6, "name": "Fries", "price": 100, "category": "Snack", "is_available": True},
]

orders = []
order_counter = 1
cart = []

# -----------------------------
# Q2 - GET MENU
# -----------------------------
@app.get("/menu")
def get_menu():
    return {"total": len(menu), "items": menu}

# -----------------------------
# FIXED ROUTE ORDER (VERY IMPORTANT)
# ALL FIXED ROUTES FIRST
# -----------------------------

# Q5 - SUMMARY
@app.get("/menu/summary")
def menu_summary():
    available = [i for i in menu if i["is_available"]]
    unavailable = [i for i in menu if not i["is_available"]]
    categories = list(set(i["category"] for i in menu))

    return {
        "total": len(menu),
        "available": len(available),
        "unavailable": len(unavailable),
        "categories": categories
    }

# Q10 - FILTER
@app.get("/menu/filter")
def filter_menu(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    is_available: Optional[bool] = None
):
    filtered = menu

    if category is not None:
        filtered = [i for i in filtered if i["category"].lower() == category.lower()]

    if max_price is not None:
        filtered = [i for i in filtered if i["price"] <= max_price]

    if is_available is not None:
        filtered = [i for i in filtered if i["is_available"] == is_available]

    return {"count": len(filtered), "items": filtered}

# Q16 - SEARCH
@app.get("/menu/search")
def search_menu(keyword: str):
    result = [i for i in menu if keyword.lower() in i["name"].lower() or keyword.lower() in i["category"].lower()]

    if not result:
        return {"message": "No items found"}

    return {"total_found": len(result), "items": result}

# Q17 - SORT
@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by"}

    reverse = True if order == "desc" else False
    sorted_items = sorted(menu, key=lambda x: x[sort_by], reverse=reverse)

    return {"items": sorted_items}

# Q18 - PAGINATION
@app.get("/menu/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    data = menu[start:start + limit]
    total_pages = math.ceil(len(menu) / limit)

    return {
        "page": page,
        "limit": limit,
        "total": len(menu),
        "total_pages": total_pages,
        "items": data
    }

# Q20 - BROWSE
@app.get("/menu/browse")
def browse(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    data = menu

    if keyword:
        data = [i for i in data if keyword.lower() in i["name"].lower()]

    reverse = True if order == "desc" else False
    data = sorted(data, key=lambda x: x[sort_by], reverse=reverse)

    start = (page - 1) * limit
    paginated = data[start:start + limit]

    return {
        "total": len(data),
        "page": page,
        "items": paginated
    }

# -----------------------------
# VARIABLE ROUTE (ALWAYS LAST)
# -----------------------------
@app.get("/menu/{item_id}")
def get_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return {"error": "Item not found"}

# -----------------------------
# ORDERS
# -----------------------------
@app.get("/orders")
def get_orders():
    return {"total_orders": len(orders), "orders": orders}

# -----------------------------
# MODELS
# -----------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"

# -----------------------------
# HELPERS
# -----------------------------
def find_menu_item(item_id):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

# -----------------------------
# CREATE ORDER
# -----------------------------
@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    item = find_menu_item(order.item_id)

    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    total_price = calculate_bill(item["price"], order.quantity, order.order_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item_name": item["name"],
        "quantity": order.quantity,
        "total_price": total_price
    }

    orders.append(new_order)
    order_counter += 1

    return new_order

# -----------------------------
# CRUD
# -----------------------------
class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True

@app.post("/menu")
def add_item(item: NewMenuItem, response: Response):
    new_id = max(i["id"] for i in menu) + 1

    for i in menu:
        if i["name"].lower() == item.name.lower():
            return {"error": "Item exists"}

    new_item = {"id": new_id, **item.dict()}
    menu.append(new_item)

    response.status_code = status.HTTP_201_CREATED
    return new_item

@app.put("/menu/{item_id}")
def update_item(item_id: int, price: Optional[int] = None, is_available: Optional[bool] = None):
    item = find_menu_item(item_id)

    if not item:
        return {"error": "Item not found"}

    if price is not None:
        item["price"] = price

    if is_available is not None:
        item["is_available"] = is_available

    return item

@app.delete("/menu/{item_id}")
def delete_item(item_id: int):
    item = find_menu_item(item_id)

    if not item:
        return {"error": "Item not found"}

    menu.remove(item)
    return {"message": f"{item['name']} deleted"}

# -----------------------------
# CART
# -----------------------------
@app.post("/cart/add")
def add_to_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)

    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"cart": cart}

    cart.append({
        "item_id": item_id,
        "name": item["name"],
        "price": item["price"],
        "quantity": quantity
    })

    return {"cart": cart}

@app.get("/cart")
def view_cart():
    total = sum(i["price"] * i["quantity"] for i in cart)
    return {"cart": cart, "total": total}

@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):
    for c in cart:
        if c["item_id"] == item_id:
            cart.remove(c)
            return {"message": "Removed"}
    return {"error": "Not found"}

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest, response: Response):
    global order_counter

    if not cart:
        return {"error": "Cart empty"}

    placed = []
    total = 0

    for c in cart:
        price = c["price"] * c["quantity"]
        total += price

        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item_name": c["name"],
            "quantity": c["quantity"],
            "total_price": price
        }

        orders.append(order)
        placed.append(order)
        order_counter += 1

    cart.clear()
    response.status_code = status.HTTP_201_CREATED

    return {"orders": placed, "total": total}

# -----------------------------
# ORDER SEARCH + SORT
# -----------------------------
@app.get("/orders/search")
def search_orders(customer_name: str):
    return {"results": [o for o in orders if customer_name.lower() in o["customer_name"].lower()]}

@app.get("/orders/sort")
def sort_orders(order: str = "asc"):
    reverse = True if order == "desc" else False
    return {"orders": sorted(orders, key=lambda x: x["total_price"], reverse=reverse)}