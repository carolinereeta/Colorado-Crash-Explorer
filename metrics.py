"""Pure descriptive metrics; avoids causal claims and missing-value assumptions."""
from collections import Counter
from datetime import datetime, timedelta

EXCEL_EPOCH = datetime(1899, 12, 30)

def date_from_excel(value):
    """Parse CDOT's Excel-serial dates (or ISO dates) without guessing."""
    if value in (None, ''):
        return None
    try:
        return (EXCEL_EPOCH + timedelta(days=float(value))).date()
    except (ValueError, TypeError, OverflowError):
        try:
            return datetime.fromisoformat(str(value).replace('Z','')).date()
        except ValueError:
            return None

def severity(killed, injured):
    """Classify a crash, not individual people; unknown is not zero."""
    try:
        k = int(float(killed))
        i = int(float(injured))
    except (TypeError, ValueError):
        return 'Unknown'
    if k < 0 or i < 0:
        return 'Unknown'
    if k > 0:
        return 'Fatal'
    if i > 0:
        return 'Injury'
    return 'No injury reported'

def valid_point(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (ValueError, TypeError):
        return False
    return 36.0 <= lat <= 42.0 and -110.0 <= lon <= -101.0

def non_motorist_category(value1, value2):
    text = ' / '.join(str(v or '').lower() for v in (value1, value2))
    if 'pedestrian' in text:
        return 'Pedestrian recorded'
    if any(w in text for w in ('bicycl', 'pedalcycl', 'cyclist')):
        return 'Cyclist recorded'
    if text.strip(' /') and all(w not in text for w in ('unknown', 'none', 'not applicable')):
        return 'Other non-motorist recorded'
    return 'Not identified in selected fields'

def pct(part, total):
    return round(100.0 * part / total, 2) if total else None
