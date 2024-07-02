from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

#
# Decimals
#


def to_decimal(value):
    """Convert to a decimal with the required precision. The value can be string, float or decimal."""
    # Possible cases: string, 4.1-e7, float like 0.1999999999999 (=0.2), Decimal('4.1E-7')

    # App.config["trade"]["symbol_info"]["baseAssetPrecision"]

    n = 8
    rr = Decimal(1) / (Decimal(10) ** n)  # Result: 0.00000001
    ret = Decimal(str(value)).quantize(rr, rounding=ROUND_DOWN)
    return ret


def round_str(value, digits):
    rr = Decimal(1) / (Decimal(10) ** digits)  # Result for 8 digits: 0.00000001
    ret = Decimal(str(value)).quantize(rr, rounding=ROUND_HALF_UP)
    return f"{ret:.{digits}f}"


def round_down_str(value, digits):
    rr = Decimal(1) / (Decimal(10) ** digits)  # Result for 8 digits: 0.00000001
    ret = Decimal(str(value)).quantize(rr, rounding=ROUND_DOWN)
    return f"{ret:.{digits}f}"
