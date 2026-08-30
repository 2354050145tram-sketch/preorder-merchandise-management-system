def serialize_cart_item(item):
    product = item.product

    return {
        "cart_item_id": item.cart_item_id,
        "product_id": item.product_id,
        "preorder_id": item.preorder_id,
        "product_name": (product.product_name if product else None),
        "image": (product.image if product else None),
        "status": (product.status if product else None),
        "price": (float(product.price) if product else 0),
        "quantity": item.quantity,
        "subtotal": (float(product.price) * item.quantity if product else 0),
    }


def serialize_cart(cart):
    items = [serialize_cart_item(item) for item in cart.items]

    total = sum(item["subtotal"] for item in items)

    return {
        "cart_id": cart.cart_id,
        "user_id": cart.user_id,
        "items": items,
        "total": total,
        "total_items": sum(item["quantity"] for item in items),
    }
