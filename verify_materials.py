"""Local checks; does not connect to Snowflake or replace a Snowsight walkthrough."""
import ast
import csv
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent


class LabParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self.links = []
        self.downloads = []
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
            self.current = dict(attrs, practice=0, practice_headings=0, practice_icons=0)
            self.sections.append(self.current)
        if tag == 'div' and attrs.get('class') == 'coco-practice':
            self.current['practice'] += 1
        if tag == 'h2' and attrs.get('class') == 'coco-heading':
            self.current['practice_headings'] += 1
        if tag == 'svg' and attrs.get('class') == 'coco-icon':
            self.current['practice_icons'] += 1
            assert attrs.get('aria-hidden') == 'true'
        assert not (tag == 'details' and attrs.get('class') == 'stretch'), 'CoCo practice must not be collapsible'
        if tag in ('a', 'script', 'link'):
            self.links.append(attrs.get('href', attrs.get('src', '')))
        if tag == 'a' and 'download' in attrs:
            self.downloads.append(attrs.get('href', ''))
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
    html = (ROOT / 'index.html').read_text()
    parser.feed(html)
    assert parser.downloads.count('snowcamp-data.zip') == 2, 'Data download missing from overview or load step'
    assert 'snowcamp-materials.zip' in parser.downloads, 'Manual-upload fallback missing'
    assert 'Do not select <em>From Git repository</em>' not in html, 'Stale workspace instruction'
    bootstrap = next(block for block in parser.blocks if 'CREATE API INTEGRATION' in block)
    assert 'SNOWCAMP_GIT_INTEGRATION' in bootstrap and 'git_https_api' in bootstrap
    assert 'https://github.com/sfc-gh-gfuribondo/snowcamp-0day-lab' in bootstrap
    assert 'Public repository' in html and 'data/setup.sql' in html and 'data/load_data.sql' in html
    role_commands = re.compile(r'^\s*USE\s+(?:SECONDARY\s+)?ROLE[S]?\s+[^;]+;', re.I | re.M)
    guide_role_commands = role_commands.findall('\n'.join(parser.blocks))
    assert [command.strip() for command in guide_role_commands] == ['USE ROLE ACCOUNTADMIN;'], 'Only the initial ACCOUNTADMIN selection belongs in the guide'
    for source in ('data/setup.sql', 'data/load_data.sql', 'data/fallback_data.sql'):
        sql = (ROOT / source).read_text()
        assert not role_commands.search(sql), f'Unexpected role switch in {source}'
        assert 'ACCOUNTADMIN' in sql, f'Missing initial-role prerequisite in {source}'
    setup_source = (ROOT / 'data/setup.sql').read_text()
    setup_block = next(block for block in parser.blocks if 'CREATE COMPUTE POOL' in block)
    # The setup scripts use only full-line comments; compare code ignoring formatting.
    setup_versions = [' '.join(line.strip() for line in source.splitlines()
                               if line.strip() and not line.lstrip().startswith('--'))
                      for source in (setup_source, setup_block)]
    assert setup_versions[0] == setup_versions[1], 'Guide setup SQL differs from data/setup.sql'
    pool_statement = re.search(r'CREATE COMPUTE POOL IF NOT EXISTS LAB_STREAMLIT_POOL\b[^;]*;', setup_source)
    assert pool_statement, 'Missing non-destructive lab compute-pool creation'
    for setting in ('MIN_NODES = 1', 'MAX_NODES = 2', 'INSTANCE_FAMILY = CPU_X64_XS',
                    'AUTO_RESUME = TRUE', 'INITIALLY_SUSPENDED = TRUE', 'AUTO_SUSPEND_SECS = 60'):
        assert setting in pool_statement.group(), f'Missing compute-pool setting: {setting}'
    assert "ALTER ACCOUNT SET DEFAULT_STREAMLIT_COMPUTE_POOL = 'LAB_STREAMLIT_POOL';" in setup_source
    assert "ALTER USER SET DEFAULT_WAREHOUSE = 'LAB_WH';" in setup_source
    assert 'DESCRIBE COMPUTE POOL LAB_STREAMLIT_POOL;' in setup_source
    assert 'ALTER COMPUTE POOL LAB_STREAMLIT_POOL SUSPEND;' in parser.blocks
    assert 'facilitator-approved default compute pool' not in html
    assert 'SHOW GRANTS TO ROLE CARE_TEAM;' in html
    assert 'SHOW GRANTS OF ROLE CARE_TEAM;' in html
    assert 'expected denial' not in html and 'Both should be denied' not in html
    assert 'default role' in html and 'Workshop account only' in html
    assert len(parser.ids) == len(set(parser.ids)), 'Duplicate HTML ids'
    assert len(parser.sections) == 10
    assert 'concepts' not in parser.ids and 'Core Concepts' not in html
    assert all(section['practice'] == section['practice_headings'] == section['practice_icons'] == 1
               for section in parser.sections)
    assert sum(int(section['data-mins']) for section in parser.sections
               if section.get('data-optional') != 'true') == 82
    readme = (ROOT / 'README.md').read_text()
    assert '105-120 minutes' in html and '105-120 minutes' in readme
    assert 'If your session is 90 minutes' in html and 'For a 90-minute session' in readme
    assert '<strong>Chart</strong>' not in html, 'Unverified worksheet chart instructions returned'
    assert "which you'll learn about next" not in html
    assert 'Keep the original materials ZIP' not in html
    assert 'choose a new name if it already exists' not in html
    assert 'stop before the UPDATE' in html and 'Do not rename, replace, or drop it' in html
    guide_code = '\n'.join(parser.blocks)
    clone_names = re.findall(r'CREATE TABLE (PATIENTS_BEFORE_\w+) CLONE PATIENTS;', guide_code)
    restore_names = re.findall(r'SELECT \* FROM DAY0_LAB\.HEALTHCARE\.(PATIENTS_BEFORE_\w+);', guide_code)
    assert clone_names == restore_names == ['PATIENTS_BEFORE_EXERCISE'], 'Safety clone and recovery source must match'
    assert not re.search(r'CREATE\s+(?:OR REPLACE\s+)?TABLE\s+(?:IF NOT EXISTS\s+)?PATIENTS_BEFORE_EXERCISE',
                         guide_code.replace('CREATE TABLE PATIENTS_BEFORE_EXERCISE CLONE PATIENTS;', '')), 'Do not overwrite or silently reuse the safety clone'
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
    app_source = (ROOT / 'streamlit/streamlit_app.py').read_text()
    app_tree = ast.parse(app_source)
    assert ast.dump(ast.parse(base_app + '\n' + notes_app)) == ast.dump(app_tree)
    assert 'get_active_session' not in app_source and 'get_active_session' not in html
    assert 'use_container_width' not in app_source
    assert 'st.connection("snowflake")' in app_source
    query_calls = [node for node in ast.walk(app_tree) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute) and node.func.attr == 'query']
    assert len(query_calls) == 2
    assert all(any(keyword.arg == 'ttl' and isinstance(keyword.value, ast.Constant)
                   and keyword.value.value == 60 for keyword in call.keywords) for call in query_calls)
    assert 'WHERE NOTE_TEXT ILIKE ?' in app_source and 'params=' in app_source
    assert '+ Add new → Streamlit app' in html
    assert 'default compute pool' in html and 'private development app' in html
    assert 'Optional: deploy a Streamlit object from the workspace' in html
    assert 'warehouse-runtime' not in html and 'Warehouse runtime' not in html
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
    with ZipFile(ROOT / 'snowcamp-data.zip') as archive:
        expected = {'patients.csv', 'encounters.csv', 'clinical_notes.csv'}
        assert len(archive.namelist()) == 3 and set(archive.namelist()) == expected, 'Data ZIP must contain exactly three CSVs at root'
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name) == (ROOT / 'data' / name).read_bytes(), f'Stale data ZIP: {name}'
    with ZipFile(ROOT / 'snowcamp-materials.zip') as archive:
        assert 'snowcamp-data.zip' in archive.namelist(), 'Fallback guide needs its data download'
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name) == (ROOT / name).read_bytes(), f'Stale bundle: {name}'
    print('PASS: 10 modules, 10 visible Try it with CoCo headings/icons, 82 core minutes, delivery pacing, fixed-name clone recovery, result-table instructions, links, Python, app-code parity, CSV relationships, exact-data recovery, Git onboarding, single-role workflow, setup SQL parity, compute-pool configuration and cleanup, workspace Streamlit connection, data-only ZIP, fallback ZIP parity.')
    print('Not tested: Snowflake SQL compilation/execution, compute-pool provisioning, Snowsight UI, workspace preview, deployed Streamlit, new-session role consistency, or Snowflake recovery transaction failure behavior.')


if __name__ == '__main__':
    main()
