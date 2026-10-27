"""Game-data changes applied to the client's CSV assets at build time.

Each edit names a CSV file, the row's Name and a column. Only that one field
is rewritten; every other byte of the file stays as shipped. The file's entry
in fingerprint.json is updated so the asset list stays consistent.
"""
import hashlib
import json
from pathlib import Path

EDITS = [
    # Colette's attack: flat 1300 damage instead of 35% of the target's health.
    ('csv_logic/skills.csv', 'PercenterWeapon', 'Damage', '1300'),
    ('csv_logic/skills.csv', 'PercenterWeapon', 'PercentDamage', ''),
    # Colette reloads faster: 1800 ms per shot -> 1150 ms.
    ('csv_logic/skills.csv', 'PercenterWeapon', 'RechargeTime', '1150'),
    # Colette's Super stays stock (20% of the target's max health, 1000 to special
    # targets): her dash type always deals percent damage, and the Damage field
    # only applies to special targets such as the Heist safe.
    ('csv_logic/skills.csv', 'PercenterUlti', 'Damage', '1000'),
    ('csv_logic/skills.csv', 'PercenterUlti', 'PercentDamage', '20'),
    # Colette is hidden in v29 ("locked for Chronos"); make her obtainable.
    ('csv_logic/characters.csv', 'Percenter', 'LockedForChronos', ''),
]


def split_fields(line):
    """Split a CSV line into raw tokens, keeping each token's original quoting."""
    fields, current, quoted = [], [], False
    for char in line:
        if char == '"':
            quoted = not quoted
        if char == ',' and not quoted:
            fields.append(''.join(current))
            current = []
        else:
            current.append(char)
    fields.append(''.join(current))
    return fields


def unquote(token):
    return token[1:-1] if len(token) >= 2 and token[0] == token[-1] == '"' else token


def edit_csv(path, row_name, column, value):
    raw = path.read_bytes().decode('utf-8')
    newline = '\r\n' if '\r\n' in raw else '\n'
    lines = raw.split(newline)
    header = [unquote(token) for token in split_fields(lines[0])]
    index = header.index(column)
    for number, line in enumerate(lines[2:], start=2):
        fields = split_fields(line)
        if fields and unquote(fields[0]) == row_name:
            original = fields[index]
            fields[index] = value if value == '' or value.isdigit() else '"' + value + '"'
            lines[number] = ','.join(fields)
            changed = original != fields[index]
            path.write_bytes(newline.join(lines).encode('utf-8'))
            return changed
    raise KeyError(f'{row_name} not found in {path}')


def apply(assets):
    """Apply EDITS under an assets directory. Returns the list of changed files."""
    assets = Path(assets)
    changed = sorted({name for name, row, column, value in EDITS
                      if edit_csv(assets / name, row, column, value)})
    fingerprint_path = assets / 'fingerprint.json'
    fingerprint = json.loads(fingerprint_path.read_text(encoding='utf-8'))
    for entry in fingerprint['files']:
        if any(entry['file'] == name for name, *_ in EDITS):
            entry['sha'] = hashlib.sha1((assets / entry['file']).read_bytes()).hexdigest()
    fingerprint_path.write_text(json.dumps(fingerprint, separators=(',', ':')).replace('/', '\\/'),
                                encoding='utf-8')
    return changed
