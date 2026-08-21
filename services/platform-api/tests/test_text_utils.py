from app.text import slugify


def test_slugify_normalizes_spanish_catalog_names() -> None:
    assert slugify('  Filtro de Aceite – Motorcraft  ') == 'filtro-de-aceite-motorcraft'
    assert slugify('Transmisión 6R80 / Kit') == 'transmision-6r80-kit'
