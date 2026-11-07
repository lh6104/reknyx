"""Bounded PDF rendering from one contract-validated frozen snapshot.

No evidence URLs, HTML, or client filesystem paths are dereferenced. The worker
must enforce the separate 30-second/512-MiB process limits before calling this
function. Unsupported font glyphs fail explicitly rather than losing evidence.
"""
from io import BytesIO
import json
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from reknyx.contracts import validate

MAX_SNAPSHOT_BYTES = 10 * 1024 * 1024
MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PAGES = 500
FONT_NAME = 'ReknyxVera'


class RenderError(ValueError):
    """Rendering failed; callers retain the snapshot and record report failure."""


def _font():
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        # A package-owned constant font path, never an evidence/client path.
        path = Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf'
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(path)))
    return pdfmetrics.getFont(FONT_NAME)


def _validate(snapshot):
    encoded = json.dumps(snapshot, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_SNAPSHOT_BYTES:
        raise RenderError('Snapshot exceeds 10 MiB')
    validate('ReportSnapshot', snapshot)
    assessment_id = snapshot['assessment_id']
    if snapshot['scope']['assessment_id'] != assessment_id:
        raise RenderError('Foreign assessment scope')
    for name in ('findings', 'observations', 'artifacts', 'reviews', 'approvals'):
        for record in snapshot[name]:
            if record.get('assessment_id') != assessment_id:
                raise RenderError('Foreign assessment record')
        identities = [record['id'] for record in snapshot[name]]
        if len(set(identities)) != len(identities):
            raise RenderError('Duplicate snapshot record identity')
    artifact_ids = {record['id'] for record in snapshot['artifacts']}
    observation_ids = {record['id'] for record in snapshot['observations']}
    for observation in snapshot['observations']:
        if observation['artifact_id'] not in artifact_ids:
            raise RenderError('Missing source artifact in snapshot')
    for finding in snapshot['findings']:
        if not set(finding['observation_ids']) <= observation_ids:
            raise RenderError('Missing finding observation in snapshot')
    font = _font()
    for character in encoded.decode('utf-8'):
        if character not in '\n\r\t' and ord(character) not in font.face.charToGlyph:
            raise RenderError('Unsupported font glyph in snapshot')


def render_pdf(snapshot: dict) -> bytes:
    """Return deterministic PDF bytes without changing or reloading the snapshot."""
    _validate(snapshot)
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42,
                                topMargin=44, bottomMargin=44, pageCompression=1,
                                invariant=1, title='Reknyx assessment report', author='Reknyx')
    body = ParagraphStyle('body', fontName=FONT_NAME, fontSize=8.5, leading=12,
                          spaceAfter=5, alignment=TA_LEFT, splitLongWords=1)
    heading = ParagraphStyle('heading', parent=body, fontSize=13, leading=18,
                             spaceBefore=16, spaceAfter=10, keepWithNext=1,
                             textColor=colors.HexColor('#16324f'))
    story = []

    def paragraph(text, style=body):
        story.append(Paragraph(escape(str(text)).replace('\n', '<br/>').replace('\t', '    '), style))

    def data(label, value):
        # Structured text rather than HTML or source markup. Each leaf is a
        # separate flowable, so large evidence collections can break over pages.
        if isinstance(value, dict):
            paragraph(label)
            for key, member in value.items():
                data(key.replace('_', ' ').capitalize(), member)
        elif isinstance(value, list):
            paragraph(label + (': None recorded' if not value else ''))
            if all(isinstance(member, (str, int, float)) for member in value):
                for member in value:
                    paragraph(member)
            else:
                for index, member in enumerate(value, 1):
                    data(f'{label} {index}', member)
        else:
            paragraph(f'{label}: {"Unknown / not recorded" if value is None else value}')

    paragraph('Reknyx assessment report', heading)
    paragraph('Release status: ' + snapshot['release_status'])
    paragraph(snapshot['provenance_notice'])
    paragraph('Snapshot: ' + snapshot['id'])
    paragraph('Assessment: ' + snapshot['assessment_id'])
    paragraph('Created: ' + snapshot['created_at'])
    paragraph('1. Executive scope', heading)
    paragraph(snapshot['executive_summary'])
    data('Scope', snapshot['scope'])
    paragraph('2. Methodology and rules of engagement', heading)
    paragraph(snapshot['methodology'])
    paragraph(snapshot['rules_of_engagement'])
    data('Tools', snapshot['tool_summary'])
    paragraph('3. Severity and priorities', heading)
    data('Source severity distribution', snapshot['severity_distribution'])
    data('Finding counts', snapshot['counts'])
    paragraph('Priority is a review ordering; source confidence and technical validation remain separate.')
    paragraph('4. Findings and source evidence', heading)
    data('Findings, memberships and source values', snapshot['findings'])
    data('Source observations and raw locators', snapshot['observations'])
    data('Artifact manifests and SHA-256 hashes', snapshot['artifacts'])
    paragraph('5. Impact and remediation', heading)
    for finding in snapshot['findings']:
        paragraph(finding['title'])
        data('Contextual impact', finding['asset_impact'])
        data('Remediation', finding['remediation'])
        data('Unresolved information', finding['unknowns'])
    if not snapshot['findings']:
        paragraph('No canonical findings in this snapshot. This does not establish absence of vulnerabilities.')
    paragraph('6. Limitations and audit', heading)
    for key in ('limitations', 'assumptions', 'failures', 'approvals', 'reviews', 'assessment_started_at', 'assessment_finished_at', 'created_by', 'state_revision', 'scope_version'):
        data(key.replace('_', ' ').capitalize(), snapshot[key])
    story.append(Spacer(1, 8))

    def footer(canvas, doc):
        if doc.page > MAX_PAGES:
            raise RenderError('Report exceeds page limit')
        canvas.saveState()
        canvas.setFont(FONT_NAME, 8)
        canvas.drawString(42, 25, f'Reknyx | {snapshot["release_status"]} | Page {doc.page}')
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    output = buffer.getvalue()
    if len(output) > MAX_PDF_BYTES:
        raise RenderError('PDF exceeds 20 MiB')
    return output
