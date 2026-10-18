"""Local checks; does not connect to Snowflake or replace a Snowsight walkthrough."""
import ast
import csv
from datetime import date
from decimal import Decimal
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent


class LabParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = []
        self.links = []
        self.downloads = []
        self.ids = []
        self.current = None
        self.section_blocks = {}
        self.section_text = {}
        self.in_pre = False
        self.code = []
        self.blocks = []
        self.in_metadata = False
        self.metadata = []
        self.headings = []
        self.section_links = {}
        self.section_headings = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'section':
            self.current = dict(attrs, practice=0, practice_headings=0, practice_icons=0)
            self.sections.append(self.current)
            self.section_blocks[attrs['id']] = []
            self.section_text[attrs['id']] = []
            self.section_links[attrs['id']] = []
            self.section_headings[attrs['id']] = []
        if tag == 'div' and attrs.get('class') == 'coco-practice':
            self.current['practice'] += 1
        if tag in ('h2', 'h3') and attrs.get('class') == 'coco-heading':
            self.current['practice_headings'] += 1
        if tag == 'svg' and attrs.get('class') == 'coco-icon' and self.current:
            self.current['practice_icons'] += 1
            assert attrs.get('aria-hidden') == 'true'
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append(int(tag[1]))
            if self.current:
                self.section_headings[self.current['id']].append(int(tag[1]))
        assert not (tag == 'details' and attrs.get('class') == 'stretch'), 'CoCo practice must not be collapsible'
        if tag in ('a', 'script', 'link'):
            self.links.append(attrs.get('href', attrs.get('src', '')))
            if self.current:
                self.section_links[self.current['id']].append(attrs.get('href', attrs.get('src', '')))
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
            block = ''.join(self.code)
            self.blocks.append(block)
            if self.current:
                self.section_blocks[self.current['id']].append(block)
        if tag == 'section':
            self.current = None
        if tag == 'script':
            self.in_metadata = False

    def handle_data(self, text):
        if self.current:
            self.section_text[self.current['id']].append(text)
        if self.in_pre:
            self.code.append(text)
        if self.in_metadata:
            self.metadata.append(text)


def normalized_sql(source):
    # Lab statements contain only full-line comments, not SQL comment literals.
    return ' '.join(' '.join(line for line in source.splitlines()
                            if not line.lstrip().startswith('--')).split())


def check_notebook():
    notebook = json.loads((ROOT / 'time_travel.ipynb').read_text())
    assert (notebook['nbformat'], notebook['nbformat_minor']) == (4, 5)
    cells = notebook['cells']
    ids = [cell['id'] for cell in cells]
    assert len(ids) == len(set(ids)) and all(re.fullmatch(r'[A-Za-z0-9]{8}', cell_id) for cell_id in ids)
    assert len(cells) == 27, 'Recovery notebook cell layout changed; review the safety sequence'
    code = {}
    positions = {}
    markdown = []
    for index, cell in enumerate(cells):
        source = ''.join(cell['source'])
        assert cell['cell_type'] in ('code', 'markdown')
        if cell['cell_type'] == 'markdown':
            markdown.append(source)
            continue
        assert cell['execution_count'] is None and cell['outputs'] == [], 'Do not ship saved executions'
        metadata = cell['metadata']
        assert metadata.get('language') == 'sql', f'Cell {index} must be a native SQL cell'
        name = metadata.get('name', '')
        assert re.fullmatch(r'[a-z][a-z0-9_]*', name), f'Cell {index} needs a SQL result name'
        assert metadata.get('resultVariableName') == name
        assert name not in code, f'Duplicate SQL result name: {name}'
        # The notebook editor normalizes SQL magics into native language metadata.
        # Accept either serialization, but require any retained magic to agree.
        sql = source
        if source.startswith('%%'):
            first_line, sql = source.split('\n', 1)
            assert first_line == f'%%sql -r {name}', f'Cell {index} has inconsistent SQL magic'
        code[name] = normalized_sql(sql)
        positions[name] = index
        assert code[name].endswith(';') and code[name].count(';') == 1, f'Cell {name} must contain one statement'
        assert not re.search(r'\bUSE\s+(?:SECONDARY\s+)?ROLES?\b', sql, re.I)
        tables = re.findall(r'\b(?:FROM|INTO|CLONE|UPDATE|TABLE)\s+([A-Z_][A-Z0-9_.]*)', code[name])
        assert all(table.startswith('DAY0_LAB.HEALTHCARE.') for table in tables), (name, tables)

    expected_order = [
        'lab_context', 'starting_counts', 'original_cities', 'safety_clone',
        'save_timestamp', 'intentional_update', 'changed_cities', 'historical_cities',
        'restore_patients', 'restored_cities', 'drop_notes', 'expected_missing_table',
        'undrop_notes', 'restored_notes', 'optional_sandbox', 'recover_from_clone', 'recovery_cities',
    ]
    assert list(code) == expected_order, 'Unsafe or unexpected recovery-cell order'
    assert code['safety_clone'] == 'CREATE TABLE DAY0_LAB.HEALTHCARE.PATIENTS_BEFORE_EXERCISE CLONE DAY0_LAB.HEALTHCARE.PATIENTS;'
    assert code['save_timestamp'] == 'SET before_mistake = CURRENT_TIMESTAMP();'
    assert code['intentional_update'] == "UPDATE DAY0_LAB.HEALTHCARE.PATIENTS SET CITY = 'Boston';"
    assert 'AT(TIMESTAMP => $before_mistake)' in code['historical_cities']
    assert code['restore_patients'] == 'INSERT OVERWRITE INTO DAY0_LAB.HEALTHCARE.PATIENTS SELECT * FROM DAY0_LAB.HEALTHCARE.PATIENTS AT(TIMESTAMP => $before_mistake);'
    assert code['recover_from_clone'] == 'INSERT OVERWRITE INTO DAY0_LAB.HEALTHCARE.PATIENTS SELECT * FROM DAY0_LAB.HEALTHCARE.PATIENTS_BEFORE_EXERCISE;'
    assert code['original_cities'] == code['historical_cities'].replace(' AT(TIMESTAMP => $before_mistake)', '')
    assert code['original_cities'] == code['restored_cities'] == code['recovery_cities']
    assert code['drop_notes'] == 'DROP TABLE DAY0_LAB.HEALTHCARE.CLINICAL_NOTES;'
    assert code['undrop_notes'] == 'UNDROP TABLE DAY0_LAB.HEALTHCARE.CLINICAL_NOTES;'
    assert code['expected_missing_table'] == code['restored_notes'] == 'SELECT COUNT(*) AS NOTES FROM DAY0_LAB.HEALTHCARE.CLINICAL_NOTES;'
    assert positions['drop_notes'] + 1 == positions['expected_missing_table'] == positions['undrop_notes'] - 1
    assert code['optional_sandbox'] == 'CREATE TABLE DAY0_LAB.HEALTHCARE.PATIENTS_SANDBOX CLONE DAY0_LAB.HEALTHCARE.PATIENTS;'
    instructions = '\n'.join(markdown)
    for warning in ('ACCOUNTADMIN', 'LAB_WH', 'Do not use Run all', 'stop before the UPDATE',
                    'Do not rename, replace, or drop it', 'Do not rerun the timestamp cell',
                    'UNDROP cell directly', 'Skip the next two cells', 'Suspend', 'Export as HTML'):
        assert warning in instructions, f'Missing notebook instruction: {warning}'
    assert 'RECOVERY ONLY' in ''.join(cells[positions['recover_from_clone']]['source'])
    assert 'Skip the next two cells' in ''.join(cells[positions['recover_from_clone'] - 1]['source'])


def check_alternate(canonical, source):
    from build_guide import GuideSource, render_guide
    html = (ROOT / 'guide.html').read_text()
    assert html == render_guide(source), 'Stale alternate guide; run tools/build_materials.py'
    alternate = LabParser()
    alternate.feed(html)
    expected_order = sorted(canonical.sections, key=lambda section: section.get('data-optional') == 'true')
    assert [section['id'] for section in alternate.sections] == [section['id'] for section in expected_order]
    assert len(alternate.ids) == len(set(alternate.ids)), 'Duplicate alternate guide anchors'
    assert alternate.headings.count(1) == 1 and alternate.headings[0] == 1
    assert all(right <= left + 1 for left, right in zip(alternate.headings, alternate.headings[1:])), 'Skipped heading level'
    for section in alternate.sections:
        identifier = section['id']
        original = next(item for item in canonical.sections if item['id'] == identifier)
        for key in ('data-title', 'data-mins', 'data-optional'):
            assert section.get(key) == original.get(key), (identifier, key)
        assert section['practice'] == section['practice_headings'] == section['practice_icons'] == (0 if section['id'] == 'overview' else 1)
        assert alternate.section_blocks[identifier] == canonical.section_blocks[identifier], f'Changed code/prompt: {identifier}'
        assert alternate.section_text[identifier] == canonical.section_text[identifier], f'Changed lesson text: {identifier}'
        assert alternate.section_links[identifier] == canonical.section_links[identifier], f'Changed lesson links: {identifier}'
        assert alternate.section_headings[identifier] == [level + 1 for level in canonical.section_headings[identifier]]
    for link in alternate.links:
        if link.startswith('#'):
            assert link[1:] in alternate.ids, link
        elif link and not link.startswith(('https://', 'http://')):
            assert (ROOT / link).exists(), link
    for content in (source, html):
        parsed = GuideSource()
        parsed.feed(content)
        if content == source:
            original_logo = parsed.logo
        else:
            assert parsed.logo == original_logo, 'CoCo logo changed'
    assert 'assets/app.js' not in html and 'assets/styles.css' not in html
    assert 'assets/guide.css' in html and 'assets/guide.js' in html
    assert not re.search(r'<(?:script|img|iframe)[^>]+(?:src|srcdoc)="https?://', html), 'No external runtime assets'
    json.loads(''.join(alternate.metadata))


def main():
    parser = LabParser()
    html = (ROOT / 'index.html').read_text()
    parser.feed(html)
    check_alternate(parser, html)
    assert parser.downloads.count('snowcamp-data.zip') == 2, 'Data download missing from overview or load step'
    assert 'snowcamp-materials.zip' in parser.downloads, 'Manual-upload fallback missing'
    assert 'Do not select <em>From Git repository</em>' not in html, 'Stale workspace instruction'
    bootstrap = next(block for block in parser.blocks if 'CREATE API INTEGRATION' in block)
    assert 'SNOWCAMP_GIT_INTEGRATION' in bootstrap and 'git_https_api' in bootstrap
    assert "API_ALLOWED_PREFIXES = (\n    'https://github.com'\n  )" in bootstrap
    assert 'Public repository' in html and 'data/setup.sql' in html and 'data/load_data.sql' in html
    role_commands = re.compile(r'^\s*USE\s+(?:SECONDARY\s+)?ROLE[S]?\s+[^;]+;', re.I | re.M)
    guide_role_commands = role_commands.findall('\n'.join(parser.blocks))
    assert {command.strip() for command in guide_role_commands} == {'USE ROLE ACCOUNTADMIN;'}, 'Only ACCOUNTADMIN role statements belong in the guide'
    for source in ('data/setup.sql', 'data/load_data.sql', 'data/fallback_data.sql', 'data/teardown.sql', 'explore.sql'):
        sql = (ROOT / source).read_text()
        commands = [command.strip() for command in role_commands.findall(sql)]
        assert commands == ['USE ROLE ACCOUNTADMIN;'], f'Expected exactly one USE ROLE ACCOUNTADMIN in {source}'
        first = next(line.strip() for line in sql.splitlines()
                     if line.strip() and not line.lstrip().startswith('--'))
        assert first == 'USE ROLE ACCOUNTADMIN;', f'USE ROLE ACCOUNTADMIN must be the first statement in {source}'
    teardown = (ROOT / 'data/teardown.sql').read_text()
    for statement in ('DROP DATABASE IF EXISTS DAY0_LAB;', 'DROP ROLE IF EXISTS CARE_TEAM;',
                      'ALTER ACCOUNT UNSET DEFAULT_STREAMLIT_COMPUTE_POOL;',
                      'ALTER COMPUTE POOL IF EXISTS LAB_STREAMLIT_POOL STOP ALL;',
                      'DROP COMPUTE POOL IF EXISTS LAB_STREAMLIT_POOL;', 'ALTER USER UNSET DEFAULT_WAREHOUSE;',
                      'DROP WAREHOUSE IF EXISTS LAB_WH;', 'DROP API INTEGRATION IF EXISTS SNOWCAMP_GIT_INTEGRATION;',
                      'ALTER ACCOUNT UNSET NOTEBOOK_VNEXT_IDLE_TIMEOUT_OPTIONS_MINUTES;',
                      'SHOW SERVICES OF TYPE NOTEBOOK;', 'DROP SERVICE IF EXISTS'):
        assert statement in teardown, f'Missing teardown step: {statement}'
    assert teardown.index('STOP ALL') < teardown.index('DROP COMPUTE POOL')
    assert 'data/teardown.sql' in parser.downloads
    setup_source = (ROOT / 'data/setup.sql').read_text()
    assert "ALTER ACCOUNT SET NOTEBOOK_VNEXT_IDLE_TIMEOUT_OPTIONS_MINUTES = '15,30,60';" in setup_source
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
    assert all(section['practice'] == section['practice_headings'] == section['practice_icons'] == (0 if section['id'] == 'overview' else 1)
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
    explore = (ROOT / 'explore.sql').read_text()
    sql_blocks = parser.section_blocks['sql']
    assert len(sql_blocks) == 8, 'Expected seven lesson blocks and one CoCo prompt'
    assert normalized_sql(explore) == normalized_sql('\n'.join(sql_blocks[:-1])), 'Guide SQL Basics differs from explore.sql'
    assert re.findall(r'^-- (\d)\.', explore, re.M) == list('01234567')
    assert not re.search(r'\b(?:UPDATE|DROP|INSERT)\b', normalized_sql(explore)), 'Recovery statements do not belong in explore.sql'
    for filename in ('explore.sql', 'time_travel.ipynb'):
        assert filename in parser.downloads, f'Missing existing-workspace download: {filename}'
    for stale in ('recovery.sql', 'it is not included in the Git repository', 'Create `explore.sql` for practice'):
        assert stale not in html + readme, f'Stale instruction: {stale}'
    coco_text = ''.join(parser.section_text['coco'])
    coco_prompts = parser.section_blocks['coco']
    assert len(coco_prompts) == 3 and 'no loaded tables required' in coco_text
    assert 'return here' not in coco_text and 'DAY0_LAB.HEALTHCARE.' not in '\n'.join(coco_prompts)
    assert 'without running code or changing files' in coco_prompts[0]
    assert 'Read data/setup.sql without executing it' in coco_prompts[1]
    assert 'Wait for my answer' in coco_prompts[2] and 'SELECT using VALUES' in coco_prompts[2]
    assert 'Do not execute SQL or change anything' in coco_prompts[2]
    travel_text = ''.join(parser.section_text['timetravel'])
    assert 'time_travel.ipynb' in travel_text and 'Do not use Run all' in travel_text
    assert 'NOTEBOOK' in travel_text and 'Suspend' in travel_text
    check_notebook()
    metadata = json.loads(''.join(parser.metadata))
    assert {'type': 'file', 'path': 'data/payer_budget.csv', 'rows': 12} in metadata['dataSources']
    assert 'Get the prepopulated SQL files' not in ''.join(parser.section_text['overview'])
    for link in parser.links:
        if link.startswith('#'):
            assert link[1:] in parser.ids, link
        elif link and not link.startswith(('https://', 'http://')):
            assert (ROOT / link).exists(), link
    for source in ['tools/build_materials.py', 'tools/build_guide.py', 'tools/test_build_guide.py', 'tools/generate_data.py', 'streamlit/streamlit_app.py']:
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
    assert '+ Add new → Streamlit App' in html
    assert 'default compute pool' in html and 'private development app' in html
    assert 'Optional: deploy a Streamlit object from the workspace' in html
    assert 'warehouse-runtime' not in html and 'Warehouse runtime' not in html
    data = {}
    for name, count in [('patients', 500), ('encounters', 5000), ('clinical_notes', 1500)]:
        with (ROOT / 'data' / (name + '.csv')).open(newline='') as handle:
            data[name] = list(csv.DictReader(handle))
        assert len(data[name]) == count
    with (ROOT / 'data/payer_budget.csv').open(newline='') as handle:
        budget_reader = csv.DictReader(handle)
        assert budget_reader.fieldnames == ['BUDGET_MONTH', 'PLAN_TYPE', 'BUDGETED_CLAIMS_USD', 'MEMBER_MONTHS']
        budgets = list(budget_reader)
    assert len(budgets) == 12
    expected_budget_keys = {(f'2026-{month:02d}-01', plan) for month in range(1, 5)
                            for plan in ('Commercial', 'Medicare Advantage', 'Medicaid')}
    assert {(row['BUDGET_MONTH'], row['PLAN_TYPE']) for row in budgets} == expected_budget_keys
    assert all(date.fromisoformat(row['BUDGET_MONTH']).day == 1 for row in budgets)
    assert all(Decimal(row['BUDGETED_CLAIMS_USD']) > 0 and int(row['MEMBER_MONTHS']) > 0 for row in budgets)
    assert sum(Decimal(row['BUDGETED_CLAIMS_USD']) for row in budgets) == Decimal('1980000.00')
    budget_prompt = next(block for block in parser.section_blocks['load'] if block.startswith('Load data/payer_budget.csv'))
    for requirement in ('DAY0_LAB.HEALTHCARE.PAYER_BUDGET', 'LAB_WH', 'ACCOUNTADMIN',
                        'Wait for my approval', 'If the table already exists, stop',
                        'do not invent data or request credentials', 'Do not change PATIENTS',
                        'BUDGET_MONTH and PLAN_TYPE', 'total BUDGETED_CLAIMS_USD'):
        assert requirement in budget_prompt, f'Missing budget-load guardrail: {requirement}'
    assert 'data/payer_budget.csv' in parser.downloads
    load_text = ''.join(parser.section_text['load'])
    for checkpoint in ('new CoCo chat', '12 rows', '$1,980,000.00', 'Facilitator rehearsal required'):
        assert checkpoint in load_text, f'Missing budget instruction: {checkpoint}'
    for filename in ('setup.sql', 'load_data.sql', 'fallback_data.sql'):
        assert 'PAYER_BUDGET' not in (ROOT / 'data' / filename).read_text().upper()
    patients = {row['PATIENT_ID'] for row in data['patients']}
    encounters = {row['ENCOUNTER_ID']: row for row in data['encounters']}
    assert len(patients) == 500 and len(encounters) == 5000
    assert len({row['CITY'] for row in data['patients']}) == 10, 'Notebook expects ten original cities'
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
        expected = {
            'index.html', 'assets/app.js', 'assets/styles.css', 'streamlit/streamlit_app.py',
            'explore.sql', 'time_travel.ipynb', 'snowcamp-data.zip',
            'data/patients.csv', 'data/encounters.csv', 'data/clinical_notes.csv', 'data/payer_budget.csv',
            'data/setup.sql', 'data/load_data.sql', 'data/fallback_data.sql', 'data/teardown.sql',
            'guide.html', 'assets/guide.css', 'assets/guide.js',
        }
        assert len(archive.namelist()) == len(expected) and set(archive.namelist()) == expected, 'Fallback bundle must contain all 18 files'
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name) == (ROOT / name).read_bytes(), f'Stale bundle: {name}'
    print('PASS: both guides match in all 10 modules, prompts, SQL, links, and CoCo logos; accessible heading order; immediate Meet CoCo prompts; 82 core minutes; setup/explore SQL parity; 27-cell notebook structure and recovery order; Python; app-code parity; CSV relationships; exact-data recovery; Git onboarding; single-role workflow; compute cleanup; data-only ZIP; payer-budget CSV and loading guardrails; teardown coverage; 18-file fallback ZIP parity.')
    print('Not tested: CoCo workspace-CSV ingestion, Snowflake SQL compilation/execution, notebook import/runtime/session continuity, compute-pool provisioning, Snowsight UI, workspace preview, deployed Streamlit, new-session role consistency, or recovery transaction failure behavior.')


if __name__ == '__main__':
    main()
