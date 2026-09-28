import pytest
from core.vis_filter import mentions_vis


@pytest.mark.parametrize("text", [
    "Otok Vis dobio novi vodovod",
    "Grad Vis najavio radove",
    "Trajekt za Visa kasni dva sata",
    "Turisti stižu na otok Visom",
    "Višani traže bolju cestu",
    "Komiža slavi Filipijadu",
    "Novi restoran u Komiži",
])
def test_positive_matches(text):
    assert mentions_vis(text) is True


@pytest.mark.parametrize("text", [
    "Split dobio novi vodovod",
    "Predsjednik je visok dva metra",
    "Cijene visoke ovog ljeta",
    "Zagreb i Rijeka potpisali sporazum",
])
def test_negative_matches(text):
    assert mentions_vis(text) is False
