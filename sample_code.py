def calculate_total(items):
    """Calculate total price for all items."""
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
