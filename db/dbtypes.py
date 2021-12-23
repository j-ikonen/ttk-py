""" Functions for custom sqlite types. """

from decimal import Decimal


class DecimalSum:
    """Custom AggregateClass for sqlite3 to sum pydecimal columns."""
    def __init__(self):
        self.sum = Decimal('0.00')
    
    def step(self, value):
        self.sum += converter_decimal(value)
    
    def finalize(self):
        return adapter_decimal(self.sum)

def adapter_decimal(decimal: Decimal):
    """Adapt a decimal to bytes for insert into sqlite table."""
    if decimal is None:
        decimal = Decimal('0.00')
    return str(decimal).encode('ascii')

def converter_decimal(decimal: bytes):
    """Convert bytes from sqlite to Decimal."""
    try:
        return Decimal(decimal.decode('ascii')).quantize(Decimal('.01'))
    except AttributeError:
        return Decimal('0.00')

def decimal_add(*args):
    """Define custom function for adding Decimal arguments in sqlite queries."""
    sum = Decimal('0.00')
    for value in args:
        sum += converter_decimal(value)
    return adapter_decimal(sum)

def decimal_sub(a, b):
    """Define custom function for substracting Decimal arguments in sqlite queries."""
    return adapter_decimal(converter_decimal(a) - converter_decimal(b))

def decimal_mul(a, b):
    """Define custom function for multiplying Decimal arguments in sqlite queries."""
    return adapter_decimal(converter_decimal(a) * converter_decimal(b))

def decimal_div(a, b):
    """Define custom function for dividing Decimal arguments in sqlite queries."""
    return adapter_decimal(converter_decimal(a) / converter_decimal(b))

def material_cost(cost, add, edg, loss, discount):
    """Return the total cost per unit for the material row."""
    a = converter_decimal(cost) * (Decimal('1.00') + converter_decimal(loss))
    b = (Decimal('1.00') - converter_decimal(discount))
    c = converter_decimal(edg)
    d = converter_decimal(add)
    return adapter_decimal((a + d + c) * b)

def product_cost(part_cost, work_time, work_cost):
    """Return the products cost."""
    a = converter_decimal(part_cost)
    b = converter_decimal(work_time)
    c = converter_decimal(work_cost)
    return adapter_decimal(a + (b * c))
