"""Regression checks for independently reproduced OPS001/OPS002."""
from contextlib import closing
from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from services.tideglass_service.health import (CheckError, Thresholds, _table_definition,
    health, require_existing_database)
from services.tideglass_service.storage import Database


class SchemaClockRepairTests(unittest.TestCase):
    def test_table_definition_preserves_literals_and_checks(self):
        with closing(sqlite3.connect(':memory:')) as a, closing(sqlite3.connect(':memory:')) as b:
            a.execute("CREATE TABLE marker(value TEXT DEFAULT 'A B' CHECK(value != 'x'))")
            b.execute("create table marker ( value text default 'A B' /* same */ check (value != 'x') )")
            self.assertEqual(_table_definition(a,'marker'),_table_definition(b,'marker'))
            b.execute('DROP TABLE marker')
            b.execute("CREATE TABLE marker(value TEXT DEFAULT 'a b' CHECK(value != 'x'))")
            self.assertNotEqual(_table_definition(a,'marker'),_table_definition(b,'marker'))
            b.execute('DROP TABLE marker')
            b.execute("CREATE TABLE marker(value TEXT DEFAULT 'A B' CHECK(value = 'x'))")
            self.assertNotEqual(_table_definition(a,'marker'),_table_definition(b,'marker'))

    def test_semantic_schema_rejects_conflict_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'db.sqlite3';database=Database(path)
            with database.transaction() as db:
                db.execute('DROP TABLE flags')
                db.execute('CREATE TABLE flags(name TEXT PRIMARY KEY ON CONFLICT REPLACE, enabled INTEGER NOT NULL)')
                db.executemany('INSERT INTO flags VALUES(?,1)',[(v,) for v in ('cloud','purchases','ads','telemetry')])
            before=path.read_bytes()
            with self.assertRaises(CheckError):require_existing_database(path)
            self.assertEqual(before,path.read_bytes())

    def test_missing_or_unrecognized_explicit_indexes_are_refused(self):
        for statement in ['DROP INDEX snapshot_parents',
                          "CREATE INDEX unexpected_expression ON accounts(json_extract(seed,'$'))",
                          'CREATE INDEX extra_index ON accounts(created)']:
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'db.sqlite3';database=Database(path)
                with database.transaction() as db:db.execute(statement)
                before=path.read_bytes()
                with self.assertRaises(CheckError):require_existing_database(path)
                self.assertEqual(before,path.read_bytes())

    def test_reserved_prefix_matching_does_not_hide_user_objects(self):
        for statement in ['CREATE TABLE sqliteXhidden(value INTEGER)',
                          'CREATE INDEX sqliteXhidden ON accounts(created)',
                          'CREATE TRIGGER sqliteXhidden AFTER INSERT ON accounts BEGIN DELETE FROM accounts; END']:
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'db.sqlite3';database=Database(path)
                with database.transaction() as db:db.execute(statement)
                before=path.read_bytes()
                with self.assertRaises(CheckError):require_existing_database(path)
                self.assertEqual(before,path.read_bytes())

    def test_future_only_rows_are_alerted_without_quality_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'db.sqlite3';database=Database(path)
            with database.transaction() as db:
                db.execute('INSERT INTO accounts(id,recovery_hash,created,consent) VALUES(?,?,?,1)',('fixture','secret-hash',100))
                db.execute('INSERT INTO telemetry VALUES(?,?,?,?,?,?,?)',
                    ('fixture','future','session','save_result',201,201,
                     json.dumps({'properties':{'platform':'ios','outcome':'saved'}})))
            result=health(path,now=200,thresholds=replace(Thresholds(),minimum_free_bytes=1,minimum_free_fraction=0))
            rows={r['name']:r for r in result['checks']}
            self.assertEqual(result['status'],'critical')
            self.assertEqual(rows['telemetry_timestamps']['count'],1)
            self.assertEqual(rows['critical_flows']['sample_count'],0)
            self.assertEqual(rows['critical_flows']['status'],'unknown')
            self.assertIsNone(rows['critical_flows']['failure_fraction'])
            self.assertNotIn('secret-hash',json.dumps(result))


if __name__=='__main__':unittest.main()
