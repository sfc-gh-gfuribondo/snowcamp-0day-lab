"""Local checks; does not connect to Snowflake or replace a Snowsight walkthrough."""
import ast
import csv
import json
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent


class LabParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self.links = []
        self.ids = []
        self.current = None
        self.in_pre = False
        self.code = []
        self.blocks = []
        self.in_metadata = False
        self.metadata = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'section':
            self.current = dict(attrs, stretch=0)
            self.sections.append(self.current)
        if tag == 'details' and attrs.get('class') == 'stretch':
            self.current['stretch'] += 1
        if tag in ('a', 'script', 'link'):
            self.links.append(attrs.get('href', attrs.get('src', '')))
        if tag == 'pre':
            self.in_pre = True
            self.code = []
        if tag == 'script' and attrs.get('id') == 'snowflake-report-metadata':
            self.in_metadata = True
        assert not any(key.startswith('on') for key in attrs), 'Inline event handler'

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_pre = False
            self.blocks.append(''.join(self.code))
        if tag == 'script':
            self.in_metadata = False

    def handle_data(self, text):
        if self.in_pre:
            self.code.append(text)
        if self.in_metadata:
            self.metadata.append(text)


def main():
    parser = LabParser()
    parser.feed((ROOT / 'index.html').read_text())
    assert len(parser.ids) == len(set(parser.ids)), 'Duplicate HTML ids'
    assert len(parser.sections) == 11
    assert all(section['stretch'] == 1 for section in parser.sections)
    assert sum(int(section['data-mins']) for section in parser.sections
               if section.get('data-optional') != 'true') == 90
    json.loads(''.join(parser.metadata))
    for link in parser.links:
        if link.startswith('#'):
            assert link[1:] in parser.ids, link
        elif link and not link.startswith(('https://', 'http://')):
            assert (ROOT / link).exists(), link
    for source in ['build_materials.py', 'data/generate_data.py', 'streamlit/streamlit_app.py']:
        ast.parse((ROOT / source).read_text())
    base_app = next(block for block in parser.blocks if block.startswith('import streamlit'))
    notes_app = next(block for block in parser.blocks if block.startswith('st.subheader("Search clinical notes")'))
    assert ast.dump(ast.parse(base_app + '\n' + notes_app)) == ast.dump(
        ast.parse((ROOT / 'streamlit/streamlit_app.py').read_text()))
    data = {}
    for name, count in [('patients', 500), ('encounters', 5000), ('clinical_notes', 1500)]:
        with (ROOT / 'data' / (name + '.csv')).open(newline='') as handle:
            data[name] = list(csv.DictReader(handle))
        assert len(data[name]) == count
    patients = {row['PATIENT_ID'] for row in data['patients']}
    encounters = {row['ENCOUNTER_ID']: row for row in data['encounters']}
    assert len(patients) == 500 and len(encounters) == 5000
    assert all(row['PATIENT_ID'] in patients for row in data['encounters'])
    assert all(encounters[row['ENCOUNTER_ID']]['PATIENT_ID'] == row['PATIENT_ID']
               for row in data['clinical_notes'])
    from build_materials import sql_value
    fallback = (ROOT / 'data/fallback_data.sql').read_text()
    assert fallback.count('INSERT OVERWRITE INTO ') == 3
    for rows in data.values():
        for row in rows:
            assert '(' + ','.join(sql_value(value) for value in row.values()) + ')' in fallback
    assert 'INSERT INTO' not in (ROOT / 'data/setup.sql').read_text()
    with ZipFile(ROOT / 'snowcamp-materials.zip') as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name) == (ROOT / name).read_bytes(), f'Stale bundle: {name}'
    print('PASS: 11 modules, 11 Try it with CoCo sections, 90 core minutes, links, Python, app-code parity, CSV relationships, exact-data recovery, ZIP parity.')
    print('Not tested: Snowsight UI, deployed Streamlit, actual role-denial execution, or Snowflake recovery transaction failure behavior.')


if __name__ == '__main__':
    main()
