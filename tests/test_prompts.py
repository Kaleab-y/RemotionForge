import pathlib


def test_prompts_exist_and_non_empty():
    p = pathlib.Path('.archon/prompts')
    assert p.is_dir(), f"Missing prompts dir: {p}"
    files = ['fetch-source.md', 'plan-video.md', 'qa-review.md', 'summarize.md']
    for fn in files:
        fp = p / fn
        assert fp.exists(), f"Missing prompt file: {fp}"
        text = fp.read_text(encoding='utf-8').strip()
        assert text, f"Prompt file {fp} is empty"
