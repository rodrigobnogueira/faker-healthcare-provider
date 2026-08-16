"""Generated patient identifiers, and the check-digit arithmetic behind them.

Right now that means the **NHS Number**, the ten-digit identifier used across the health
service in England, Wales and the Isle of Man. It is here because the identifier a
consumer needs in a test record has to satisfy the same checksum the software under test
validates it with — a random ten-digit string fails the first validator it meets, which
is exactly the bug a fake-data library should not make you find.

Reserved ranges, and why the default is the test one
----------------------------------------------------
A generated identifier that is *valid* is, by construction, an identifier that could
belong to a real person. That is the whole hazard: a synthetic record carrying a
checksum-valid NHS number can be mistaken for a real one, matched against a real one, or
loaded into something that treats it as real.

So the default is the range NHS England reserves for exactly this: numbers beginning
**999**, which are never issued to a patient. `nhs_number()` returns one of those unless
you deliberately ask otherwise, and `nhs_number(official_test_range=False)` — which is
the opt-in, not the default — draws from the full range and is documented as capable of
colliding with a living person's number. Use it only when you are testing something that
rejects the 999 prefix.

This is the general rule for any identifier this package learns to generate: default to
whatever range the issuing authority has reserved for testing, and make the unreserved
mode explicit at the call site. AGENTS.md and CONTRIBUTING.md carry it.

The algorithm
-------------
Modulus 11, implemented from the published specification in the NHS Data Model and
Dictionary, attribute "NHS NUMBER"
(https://www.datadictionary.nhs.uk/attributes/nhs_number.html):

1. multiply each of the first nine digits by its weighting factor — the first digit by
   10, the second by 9, and so on down to the ninth by 2;
2. add the nine products together;
3. take the remainder of that total divided by 11;
4. subtract the remainder from 11; the result is the check digit;
5. a result of 11 means the check digit is 0;
6. a result of 10 means the number is **invalid** — such a nine-digit stem is never
   issued, and this module redraws rather than emitting one.

The check digit is the tenth digit. NHS numbers are conventionally written in 3-3-4
groups ("999 123 4567"), which is the form `nhs_number()` returns; `nhs_number_digits()`
returns the same value unformatted.
"""

__all__ = [
    "NHS_NUMBER_LENGTH",
    "NHS_TEST_RANGE_PREFIX",
    "format_nhs_number",
    "nhs_check_digit",
    "nhs_number_digits",
    "nhs_number_is_valid",
]


NHS_NUMBER_LENGTH = 10

# The range NHS England reserves for test data; never allocated to a real patient.
NHS_TEST_RANGE_PREFIX = "999"

# Weighting factors for the first nine digits, in order: 10, 9, 8, ... 2.
_WEIGHTS = tuple(range(10, 1, -1))

# What step 6 returns for a stem that must be redrawn.
_INVALID_CHECK_DIGIT = 10


def nhs_check_digit(stem: str) -> int:
    """Return the Modulus 11 check digit for the first nine digits of an NHS number.

    Args:
        stem: exactly nine digits.

    Returns:
        The check digit 0-9, or 10 to mean "this stem is invalid and must not be used" —
        step 6 of the specification in this module's docstring. Callers redraw on 10;
        they must not truncate it to a single digit.

    Raises:
        ValueError: if the stem is not exactly nine digits.
    """
    if len(stem) != NHS_NUMBER_LENGTH - 1 or not stem.isdigit():
        raise ValueError(f"An NHS number stem is exactly {NHS_NUMBER_LENGTH - 1} digits, got {stem!r}")
    total = sum(int(digit) * weight for digit, weight in zip(stem, _WEIGHTS))
    check_digit = 11 - (total % 11)
    if check_digit == 11:
        return 0
    return check_digit


def nhs_number_is_valid(number: str) -> bool:
    """Whether a string is a valid NHS number, spaces and dashes ignored."""
    digits = nhs_number_digits(number)
    if len(digits) != NHS_NUMBER_LENGTH or not digits.isdigit():
        return False
    check_digit = nhs_check_digit(digits[:-1])
    return check_digit != _INVALID_CHECK_DIGIT and check_digit == int(digits[-1])


def nhs_number_digits(number: str) -> str:
    """Return an NHS number with its conventional grouping (or any dashes) stripped."""
    return number.replace(" ", "").replace("-", "")


def format_nhs_number(digits: str) -> str:
    """Group ten digits the conventional way: three, three, four."""
    if len(digits) != NHS_NUMBER_LENGTH or not digits.isdigit():
        raise ValueError(f"An NHS number is exactly {NHS_NUMBER_LENGTH} digits, got {digits!r}")
    return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
