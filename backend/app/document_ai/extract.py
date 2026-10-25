"""Local extraction. Confidence measures OCR, never authenticity."""
import io, re, hashlib
from datetime import datetime, timezone
import pymupdf as fitz
from PIL import Image, UnidentifiedImageError
import pytesseract
import cv2
import numpy as np

MAX_PAGES = 60
Image.MAX_IMAGE_PIXELS = 25_000_000


def inspect_file(data: bytes, limit: int):
    if not data or len(data) > limit: raise ValueError('Empty file or upload exceeds size limit')
    try:
        if data.startswith(b'%PDF-'):
            with fitz.open(stream=data, filetype='pdf') as doc:
                if doc.is_encrypted or not 0 < len(doc) <= MAX_PAGES:
                    raise ValueError('Encrypted PDF or page limit exceeded (60)')
                # Reject active content and embedded attachments; originals are never rewritten.
                if doc.embfile_count() or b'/JavaScript' in data or b'/JS ' in data:
                    raise ValueError('Active content or PDF attachments are not permitted')
                doc[0].get_text()
            mime = 'application/pdf'
        else:
            with Image.open(io.BytesIO(data)) as im:
                if im.width * im.height > 25_000_000: raise ValueError('Image exceeds 25 million pixel limit')
                if im.format not in ('PNG', 'JPEG'): raise ValueError('Only PDF, PNG and JPEG are supported')
                im.verify()
                mime = 'image/png' if im.format == 'PNG' else 'image/jpeg'
    except (RuntimeError, UnidentifiedImageError, OSError) as exc:
        raise ValueError('Corrupt or unsupported document') from exc
    return mime, hashlib.sha256(data).hexdigest()


def ocr(image):
    result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, timeout=45)
    words, lines = [], {}
    for i, (text, confidence) in enumerate(zip(result['text'], result['conf'])):
        if not text.strip() or float(confidence) < 0: continue
        words.append((text, float(confidence)))
        # Preserve OCR line structure: flattening lines corrupts field boundaries.
        key = tuple(result.get(name, [0] * len(result['text']))[i] for name in ('block_num','par_num','line_num'))
        lines.setdefault(key, []).append(text)
    return '\n'.join(' '.join(tokens) for tokens in lines.values()), (sum(c for _, c in words) / len(words) / 100 if words else None)

PATTERNS = {
    'institution_identifier': r'Institution\s*(?:ID|Identifier)\s*:\s*([^\n]+)',
    'institution_name': r'Institution\s*Name\s*:\s*([^\n]+)',
    'reference_number': r'Reference\s*(?:Number|No)?\s*:\s*([^\n]+)',
    'expiry_date': r'(?:Expiry|Valid Until)\s*(?:Date)?\s*:\s*(\d{4}-\d{2}-\d{2})',
    'faculty_count': r'Faculty\s*Count\s*:\s*(\d+)',
    'intake': r'Intake\s*:\s*(\d+)',
    'payment_status': r'Payment\s*Status\s*:\s*([^\n]+)',
}

def normalize(name, value):
    value = ' '.join(value.split())
    if name in ('institution_identifier','reference_number','payment_status'): return value.upper()
    if name in ('faculty_count','intake'): return str(int(value))
    return value


def image_hash(image):
    gray = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2GRAY)
    small = cv2.resize(gray, (9, 8))
    bits = small[:, 1:] > small[:, :-1]
    return f'{int("".join("1" if x else "0" for x in bits.flatten()), 2):016x}'


def extract(data: bytes, mime: str, engine='tesseract'):
    pages, metadata, visual_hash = [], {}, None
    if mime == 'application/pdf':
        with fitz.open(stream=data, filetype='pdf') as doc:
            metadata = doc.metadata
            for i, page in enumerate(doc):
                text, confidence = page.get_text(), None
                if len(text.strip()) < 30:
                    if engine != 'tesseract': raise ValueError('Configure supported OCR engine: tesseract')
                    if page.rect.width * page.rect.height * 2.25 > 25_000_000: raise ValueError('Rendered page exceeds pixel limit')
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    if pix.width * pix.height > 25_000_000: raise ValueError('Rendered page exceeds pixel limit')
                    text, confidence = ocr(Image.frombytes('RGB', [pix.width, pix.height], pix.samples))
                pages.append((i + 1, text, confidence))
    else:
        with Image.open(io.BytesIO(data)) as image:
            visual_hash = image_hash(image)
            text, confidence = ocr(image)
            pages.append((1, text, confidence))
            metadata = {'format': image.format, 'size': image.size}
    fields = []
    for number, text, confidence in pages:
        for name, pattern in PATTERNS.items():
            for match in re.finditer(pattern, text, re.I):
                fields.append({'field_name': name, 'raw_value': match[1].strip(),
                    'normalized_value': normalize(name, match[1]), 'page_number': number,
                    'excerpt': match[0][:500], 'confidence': confidence,
                    'processed_at': datetime.now(timezone.utc).isoformat()})
    content = ' '.join(text for _, text, _ in pages).lower()
    classification = next((kind for token, kind in [('faculty list','faculty_list'),('certificate','certificate'),('infrastructure','infrastructure'),('undertaking','undertaking'),('payment','payment')] if token in content), 'other')
    return {'fields': fields, 'metadata': metadata, 'visual_hash': visual_hash,
            'classification': classification, 'page_count': len(pages), 'text_length': len(content)}
