# -*- coding: utf-8 -*-
"""QGIS Unit tests for QgsSpatialiteProvider

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
__author__ = 'Vincent Mora'
__date__ = '09/07/2013'
__copyright__ = 'Copyright 2013, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import qgis  # NOQA

import os
import shutil
import tempfile

from qgis.core import QgsVectorLayer, QgsPoint, QgsFeature

from qgis.testing import start_app, unittest
from utilities import unitTestDataPath
from providertestbase import ProviderTestCase
from PyQt.QtCore import QSettings

try:
    from pyspatialite import dbapi2 as sqlite3
except ImportError:
    print("You should install pyspatialite to run the tests")
    raise ImportError

# Convenience instances in case you may need them
start_app()
TEST_DATA_DIR = unitTestDataPath()


def die(error_message):
    raise Exception(error_message)


class TestQgsSpatialiteProvider(unittest.TestCase, ProviderTestCase):

    @classmethod
    def setUpClass(cls):
        """Run before all tests"""
        # setup provider for base tests
        cls.vl = QgsVectorLayer('dbname=\'{}/provider/spatialite.db\' table="somedata" (geom) sql='.format(TEST_DATA_DIR), 'test', 'spatialite')
        assert(cls.vl.isValid())
        cls.provider = cls.vl.dataProvider()

        cls.vl_poly = QgsVectorLayer('dbname=\'{}/provider/spatialite.db\' table="somepolydata" (geom) sql='.format(TEST_DATA_DIR), 'test', 'spatialite')
        assert(cls.vl_poly.isValid())
        cls.poly_provider = cls.vl_poly.dataProvider()

        # create test db
        cls.dbname = os.path.join(tempfile.gettempdir(), "test.sqlite")
        if os.path.exists(cls.dbname):
            os.remove(cls.dbname)
        con = sqlite3.connect(cls.dbname, isolation_level=None)
        cur = con.cursor()
        cur.execute("BEGIN")
        sql = "SELECT InitSpatialMetadata()"
        cur.execute(sql)

        # simple table with primary key
        sql = "CREATE TABLE test_pg (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL)"
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('test_pg', 'geometry', 4326, 'POLYGON', 'XY')"
        cur.execute(sql)
        sql = "INSERT INTO test_pg (id, name, geometry) "
        sql += "VALUES (1, 'toto', GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
        cur.execute(sql)

        # table with multiple column primary key
        sql = "CREATE TABLE test_pg_mk (id INTEGER NOT NULL, name TEXT NOT NULL, PRIMARY KEY(id,name))"
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('test_pg_mk', 'geometry', 4326, 'POLYGON', 'XY')"
        cur.execute(sql)
        sql = "INSERT INTO test_pg_mk (id, name, geometry) "
        sql += "VALUES (1, 'toto', GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
        cur.execute(sql)

        # simple table with primary key
        sql = "CREATE TABLE test_q (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL)"
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('test_q', 'geometry', 4326, 'POLYGON', 'XY')"
        cur.execute(sql)
        sql = "INSERT INTO test_q (id, name, geometry) "
        sql += "VALUES (11, 'toto', GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
        cur.execute(sql)
        sql = "INSERT INTO test_q (id, name, geometry) "
        sql += "VALUES (21, 'toto', GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
        cur.execute(sql)

        # simple table with a geometry column named 'Geometry'
        sql = "CREATE TABLE test_n (Id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL)"
        cur.execute(sql)
        sql = "SELECT AddGeometryColumn('test_n', 'Geometry', 4326, 'POLYGON', 'XY')"
        cur.execute(sql)
        sql = "INSERT INTO test_n (id, name, geometry) "
        sql += "VALUES (1, 'toto', GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
        cur.execute(sql)
        sql = "INSERT INTO test_n (id, name, geometry) "
        sql += "VALUES (2, 'toto', GeomFromText('POLYGON((0 0,1 0,1 1,0 1,0 0))', 4326))"
        cur.execute(sql)

        cur.execute("COMMIT")
        con.close()

    @classmethod
    def tearDownClass(cls):
        """Run after all tests"""
        # for the time being, keep the file to check with qgis
        # if os.path.exists(cls.dbname) :
        #    os.remove(cls.dbname)
        pass

    def setUp(self):
        """Run before each test."""
        pass

    def tearDown(self):
        """Run after each test."""
        pass

    def enableCompiler(self):
        QSettings().setValue(u'/qgis/compileExpressions', True)

    def disableCompiler(self):
        QSettings().setValue(u'/qgis/compileExpressions', False)

    def test_SplitFeature(self):
        """Create spatialite database"""
        layer = QgsVectorLayer("dbname=%s table=test_pg (geometry)" % self.dbname, "test_pg", "spatialite")
        assert(layer.isValid())
        assert(layer.hasGeometryType())
        layer.startEditing()
        layer.splitFeatures([QgsPoint(0.5, -0.5), QgsPoint(0.5, 1.5)], 0) == 0 or die("error in split")
        layer.splitFeatures([QgsPoint(-0.5, 0.5), QgsPoint(1.5, 0.5)], 0) == 0 or die("error in split")
        if not layer.commitChanges():
            die("this commit should work")
        layer.featureCount() == 4 or die("we should have 4 features after 2 split")

    def xtest_SplitFeatureWithFailedCommit(self):
        """Create spatialite database"""
        layer = QgsVectorLayer("dbname=%s table=test_pg_mk (geometry)" % self.dbname, "test_pg_mk", "spatialite")
        assert(layer.isValid())
        assert(layer.hasGeometryType())
        layer.startEditing()
        layer.splitFeatures([QgsPoint(0.5, -0.5), QgsPoint(0.5, 1.5)], 0) == 0 or die("error in split")
        layer.splitFeatures([QgsPoint(-0.5, 0.5), QgsPoint(1.5, 0.5)], 0) == 0 or die("error in split")
        if layer.commitChanges():
            die("this commit should fail")
        layer.rollBack()
        feat = QgsFeature()
        it = layer.getFeatures()
        it.nextFeature(feat)
        ref = [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]
        res = feat.geometry().asPolygon()
        for ring1, ring2 in zip(ref, res):
            for p1, p2 in zip(ring1, ring2):
                for c1, c2 in zip(p1, p2):
                    c1 == c2 or die("polygon has been altered by failed edition")

    def test_queries(self):
        """Test loading of query-based layers"""

        # a query with a geometry, but no unique id
        # the id will be autoincremented
        l = QgsVectorLayer("dbname=%s table='(select * from test_q)' (geometry)" % self.dbname, "test_pg_query1", "spatialite")
        assert(l.isValid())
        # the id() is autoincremented
        sum_id1 = sum(f.id() for f in l.getFeatures())
        # the attribute 'id' works
        sum_id2 = sum(f.attributes()[0] for f in l.getFeatures())
        assert(sum_id1 == 3)   # 1+2
        assert(sum_id2 == 32)  # 11 + 21

        # and now with an id declared
        l = QgsVectorLayer("dbname=%s table='(select * from test_q)' (geometry) key='id'" % self.dbname, "test_pg_query1", "spatialite")
        assert(l.isValid())
        sum_id1 = sum(f.id() for f in l.getFeatures())
        sum_id2 = sum(f.attributes()[0] for f in l.getFeatures())
        assert(sum_id1 == 32)
        assert(sum_id2 == 32)

        # a query, but no geometry
        l = QgsVectorLayer("dbname=%s table='(select id,name from test_q)' key='id'" % self.dbname, "test_pg_query1", "spatialite")
        assert(l.isValid())
        sum_id1 = sum(f.id() for f in l.getFeatures())
        sum_id2 = sum(f.attributes()[0] for f in l.getFeatures())
        assert(sum_id1 == 32)
        assert(sum_id2 == 32)

    def test_case(self):
        """Test case sensitivity issues"""
        l = QgsVectorLayer("dbname=%s table='test_n' (geometry) key='id'" % self.dbname, "test_n1", "spatialite")
        assert(l.isValid())
        assert(l.dataProvider().fields().count() == 2)
        fields = [f.name() for f in l.dataProvider().fields()]
        assert('Geometry' not in fields)

    def test_invalid_iterator(self):
        """ Test invalid iterator """
        corrupt_dbname = self.dbname + '.corrupt'
        shutil.copy(self.dbname, corrupt_dbname)
        layer = QgsVectorLayer("dbname=%s table=test_pg (geometry)" % corrupt_dbname, "test_pg", "spatialite")
        # Corrupt the database
        open(corrupt_dbname, 'wb').write('')
        layer.getFeatures()
        layer = None
        os.unlink(corrupt_dbname)

if __name__ == '__main__':
    unittest.main()
