def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price'] * item['qty']
    return total

def get_discount(total):
    if total > 100:
        return total * 0.1
    else:
        return 0

def process_order(items):
    total = calculate_total(items)
    discount = get_discount(total)
    final = total - discount
    print(f"Total: {total}, Discount: {discount}, Final: {final}")
    return final

def validate_item(item):
    """Validate item has required fields."""
    if item['price'] < 0:
        return False
    if item['qty'] < 0:
        return False
    return True

def apply_coupon(total, coupon_code):
    """Apply coupon code to total."""
    discounts = {'SAVE10': 0.10, 'SAVE20': 0.20, 'HALF': 0.50}
    if coupon_code in discounts:
        return total * (1 - discounts[coupon_code])
    return total
