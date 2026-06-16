import re

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W_NS}

START_ANCHOR = re.compile(r'^1\.\d+\.')
END_ANCHOR = re.compile(
    r'^[-–—]?\s*[Ее]диногласно\.?'
    r'|^[-–—]?\s*большинством голосов\.?'
    r'|^[-–—]?\s*решение принято\.?',
    re.IGNORECASE,
)
PROPOSED = re.compile(r'Предложено', re.IGNORECASE)
VOTING_RESULT = re.compile(r'В результате голосования', re.IGNORECASE)
ACCEPTED_DECISION = re.compile(r'Принято решение', re.IGNORECASE)

_W = f'{{{W_NS}}}'


def get_para_text(elem) -> str:
    return ''.join(t.text or '' for t in elem.iter(f'{_W}t'))


def is_start_anchor(text: str) -> bool:
    return bool(START_ANCHOR.match(text.strip()))


def is_end_anchor(text: str) -> bool:
    stripped = text.strip()
    return bool(END_ANCHOR.match(stripped))


def extract_point_number(text: str) -> str:
    m = re.match(r'(1\.\d+\.)', text.strip())
    return m.group(1) if m else ''
