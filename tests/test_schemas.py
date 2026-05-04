import pathlib


def test_schemas_present():
    base = pathlib.Path('.archon/schemas')
    assert (base / 'article.json').exists()
    assert (base / 'slug.json').exists()
    assert (base / 'audio' / 'voice-manifest.json').exists()
    assert (base / 'audio' / 'music-manifest.json').exists()
    assert (base / 'audio' / 'sfx-manifest.json').exists()
