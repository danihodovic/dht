from .revolut import transform_revolut_row


def test_revolut():
    row = [
        "18 Aug 2021 ",
        "google Play Ap  ",
        "22.99 ",
        " ",
        " ",
        " ",
        "719.76",
        "Shopping",
        "",
    ]
    assert transform_revolut_row(row) == [
        "18 Aug 2021",
        "google Play Ap",
        -22.99,
        "Shopping",
    ]


def test_revolut_with_exchange_rate():
    row = [
        "23 Aug 2021 ",
        "Glovo lunch FX Rate €1 = kn\xa07.4868",
        "Fee: €0.11 ",
        "10.66 ",
        " ",
        " HRK 79.00 ",
        " ",
        "707.47",
        "Restaurants",
        "",
    ]
    assert transform_revolut_row(row) == [
        "23 Aug 2021",
        "Glovo lunch FX Rate €1 = kn\xa07.4868",
        -10.66,
        "Restaurants",
    ]
