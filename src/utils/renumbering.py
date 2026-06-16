import re
from ..utils.anchors import W_NS

POINT_RE = re.compile(r'1\.\d+\.')
_W = f'{{{W_NS}}}'


def renumber_node(elem, new_index: int) -> bool:
    """Replace first 1.X. occurrence with 1.new_index. in elem subtree.

    Handles the case where '1.1.' is split across multiple <w:t> runs
    (e.g., '1', '.', '1', '.') by operating on character positions.
    """
    t_elems = list(elem.iter(f'{_W}t'))
    if not t_elems:
        return False

    texts = [t.text or '' for t in t_elems]
    combined = ''.join(texts)

    m = POINT_RE.search(combined)
    if not m:
        return False

    start, end = m.start(), m.end()
    replacement = f'1.{new_index}.'

    pos = 0
    first_set = False
    for i, t in enumerate(t_elems):
        t_len = len(texts[i])
        t_end = pos + t_len

        if pos >= end:
            break
        if t_end > start:
            if not first_set:
                prefix = texts[i][:max(0, start - pos)]
                if end <= t_end:
                    # Match starts AND ends inside this single element — preserve suffix
                    suffix = texts[i][end - pos:]
                    t.text = prefix + replacement + suffix
                    first_set = True
                    break
                else:
                    t.text = prefix + replacement
                    first_set = True
            else:
                # Clear chars that belonged to the old number; keep anything after match end
                after = texts[i][max(0, end - pos):]
                t.text = after
        pos = t_end

    return first_set


def renumber_text(text: str, new_index: int) -> str:
    return POINT_RE.sub(f'1.{new_index}.', text, count=1)
