import re

FIRST_ELEMENT_RE = re.compile(r'^(\s*<\s*[-\w]+)')


def add_fragment_id(html: str, fragment_id):
    return FIRST_ELEMENT_RE.sub(rf'\1 x-dvfragment-id={fragment_id} ', html)
