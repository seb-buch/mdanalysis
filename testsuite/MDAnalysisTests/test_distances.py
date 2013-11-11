# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# MDAnalysis --- http://mdanalysis.googlecode.com
# Copyright (c) 2006-2011 Naveen Michaud-Agrawal,
#               Elizabeth J. Denning, Oliver Beckstein,
#               and contributors (see website for details)
# Released under the GNU Public Licence, v2 or any higher version
#
# Please cite your use of MDAnalysis in published work:
#
#     N. Michaud-Agrawal, E. J. Denning, T. B. Woolf, and
#     O. Beckstein. MDAnalysis: A Toolkit for the Analysis of
#     Molecular Dynamics Simulations. J. Comput. Chem. 32 (2011), 2319--2327,
#     doi:10.1002/jcc.21787
#

import MDAnalysis
import MDAnalysis.core.distances

import numpy as np
from numpy.testing import *
del test
from nose.plugins.attrib import attr

from MDAnalysis.tests.datafiles import PSF,DCD



class TestDistanceArray(TestCase):
    def setUp(self):
        self.box = np.array([1.,1.,2.], dtype=np.float32)
        self.points = np.array([[0,0,0], [1,1,2], [1,0,2],  # identical under PBC
                                [0.5, 0.5, 1.5],
                                ], dtype=np.float32)
        self.ref = self.points[0:1]
        self.conf = self.points[1:]
        self.prec = 5

    def _dist(self, n, ref=None):
        if ref is None:
            ref = self.ref[0]
        else:
            ref = np.asarray(ref, dtype=np.float32)
        x = self.points[n]
        r = x - ref
        return np.sqrt(np.dot(r,r))

    def test_noPBC(self):
        d = MDAnalysis.core.distances.distance_array(self.ref, self.points)
        assert_almost_equal(d, np.array([[self._dist(0), self._dist(1), self._dist(2),
                                          self._dist(3),
                                          ]]))

    def test_PBC(self):
        d = MDAnalysis.core.distances.distance_array(self.ref, self.points, box=self.box)
        assert_almost_equal(d, np.array([[ 0., 0., 0.,
                                           self._dist(3, ref=[1,1,2]),
                                           ]]))

    def test_PBC2(self):
        a = np.array([  7.90146923, -13.72858524,   3.75326586], dtype=np.float32)
        b = np.array([ -1.36250901,  13.45423985,  -0.36317623], dtype=np.float32)
        box = np.array([5.5457325, 5.5457325, 5.5457325], dtype=np.float32)

        def mindist(a, b, box):
            x = a - b
            return np.linalg.norm(x - np.rint(x/box) * box)

        ref = mindist(a, b, box)
        val = MDAnalysis.core.distances.distance_array(np.array([a]), np.array([b]), box)[0,0]

        assert_almost_equal(val, ref, decimal=6, err_msg="Issue 151 not correct (PBC in distance array)")


class TestDistanceArrayDCD(TestCase):
    def setUp(self):
        self.universe = MDAnalysis.Universe(PSF, DCD)
        self.trajectory = self.universe.trajectory
        self.ca = self.universe.selectAtoms('name CA')
        # reasonable precision so that tests succeed on 32 and 64 bit machines
        # (the reference values were obtained on 64 bit)
        # Example:
        #   Items are not equal: wrong maximum distance value
        #   ACTUAL: 52.470254967456412
        #   DESIRED: 52.470257062419059
        self.prec = 5

    def tearDown(self):
        del self.universe
        del self.trajectory
        del self.ca

    @attr('issue')
    def test_simple(self):
        U = self.universe
        self.trajectory.rewind()
        x0 = U.atoms.coordinates(copy=True)
        self.trajectory[10]
        x1 = U.atoms.coordinates(copy=True)
        d = MDAnalysis.core.distances.distance_array(x0, x1)
        assert_equal(d.shape, (3341, 3341), "wrong shape (should be (Natoms,Natoms))")
        assert_almost_equal(d.min(), 0.11981228170520701, self.prec,
                            err_msg="wrong minimum distance value")
        assert_almost_equal(d.max(), 53.572192429459619, self.prec,
                            err_msg="wrong maximum distance value")

    def test_outarray(self):
        U = self.universe
        self.trajectory.rewind()
        x0 = U.atoms.coordinates(copy=True)
        self.trajectory[10]
        x1 = U.atoms.coordinates(copy=True)
        natoms = len(U.atoms)
        d = np.zeros((natoms, natoms), np.float64)
        MDAnalysis.core.distances.distance_array(x0, x1, result=d)
        assert_equal(d.shape, (natoms, natoms), "wrong shape, shoud be  (Natoms,Natoms) entries")
        assert_almost_equal(d.min(), 0.11981228170520701, self.prec,
                            err_msg="wrong minimum distance value")
        assert_almost_equal(d.max(), 53.572192429459619, self.prec,
                            err_msg="wrong maximum distance value")

    def test_periodic(self):
        # boring with the current dcd as that has no PBC
        U = self.universe
        self.trajectory.rewind()
        x0 = U.atoms.coordinates(copy=True)
        self.trajectory[10]
        x1 = U.atoms.coordinates(copy=True)
        d = MDAnalysis.core.distances.distance_array(x0, x1, box=U.coord.dimensions)
        assert_equal(d.shape, (3341, 3341), "should be square matrix with Natoms entries")
        assert_almost_equal(d.min(), 0.11981228170520701, self.prec,
                            err_msg="wrong minimum distance value with PBC")
        assert_almost_equal(d.max(), 53.572192429459619, self.prec,
                            err_msg="wrong maximum distance value with PBC")


class TestSelfDistanceArrayDCD(TestCase):
    def setUp(self):
        self.universe = MDAnalysis.Universe(PSF, DCD)
        self.trajectory = self.universe.trajectory
        self.ca = self.universe.selectAtoms('name CA')
        # see comments above on precision
        self.prec = 5

    def tearDown(self):
        del self.universe
        del self.trajectory
        del self.ca

    def test_simple(self):
        U = self.universe
        self.trajectory.rewind()
        x0 = U.atoms.coordinates(copy=True)
        d = MDAnalysis.core.distances.self_distance_array(x0)
        N = 3341 * (3341 - 1) / 2
        assert_equal(d.shape, (N,), "wrong shape (should be (Natoms*(Natoms-1)/2,))")
        assert_almost_equal(d.min(), 0.92905562402529318, self.prec,
                            err_msg="wrong minimum distance value")
        assert_almost_equal(d.max(), 52.4702570624190590, self.prec,
                            err_msg="wrong maximum distance value")

    def test_outarray(self):
        U = self.universe
        self.trajectory.rewind()
        x0 = U.atoms.coordinates(copy=True)
        natoms = len(U.atoms)
        N = natoms*(natoms-1) / 2
        d = np.zeros((N,), np.float64)
        MDAnalysis.core.distances.self_distance_array(x0, result=d)
        assert_equal(d.shape, (N,), "wrong shape (should be (Natoms*(Natoms-1)/2,))")
        assert_almost_equal(d.min(), 0.92905562402529318, self.prec,
                            err_msg="wrong minimum distance value")
        assert_almost_equal(d.max(), 52.4702570624190590, self.prec,
                            err_msg="wrong maximum distance value")

    def test_periodic(self):
        # boring with the current dcd as that has no PBC
        U = self.universe
        self.trajectory.rewind()
        x0 = U.atoms.coordinates(copy=True)
        natoms = len(U.atoms)
        N = natoms*(natoms-1) / 2
        d = MDAnalysis.core.distances.self_distance_array(x0, box=U.coord.dimensions)
        assert_equal(d.shape, (N,), "wrong shape (should be (Natoms*(Natoms-1)/2,))")
        assert_almost_equal(d.min(), 0.92905562402529318, self.prec,
                            err_msg="wrong minimum distance value with PBC")
        assert_almost_equal(d.max(), 52.4702570624190590, self.prec,
                            err_msg="wrong maximum distance value with PBC")



class TestCythonFunctions(TestCase):
    # Unit tests for calc_bonds calc_angles and calc_torsions in core.distances
    # Tests both numerical results as well as input types as Cython will silently produce nonsensical results
    # if given wrong data types otherwise.
    def setUp(self):
        self.prec = 5
        self.box = np.array([10., 10., 10.], dtype=np.float32)
        # dummy atom data
        self.a = np.array([[0., 0., 0.],
                           [0., 0., 0.],
                           [0., 11., 0.],
                           [1., 1., 1.]
                           ], dtype=np.float32)
        self.b = np.array([[0., 0., 0.],
                           [1., 1., 1.],
                           [0., 0., 0.],
                           [29., -21., 99.]
                           ], dtype=np.float32)
        self.c = np.array([[0., 0., 0.],
                           [2., 2., 2.],
                           [11., 0., 0.],
                           [1., 9., 9.]
                           ], dtype=np.float32)
        self.d = np.array([[0., 0., 0.],
                           [3., 3., 3.],
                           [11., -11., 0.],
                           [65., -65., 65.]
                           ], dtype=np.float32)
        self.wrongtype = np.array([[0., 0., 0.],
                                   [3., 3., 3.],
                                   [3., 3., 3.],
                                   [3., 3., 3.]
                                  ], dtype=np.float64) #declared as float64 and should raise TypeError
        self.wronglength = np.array([[0., 0., 0.],
                                     [3., 3., 3.]
                                    ], dtype=np.float32)#has a different length to other inputs and should raise ValueError

    def tearDown(self):
        del self.box
        del self.a
        del self.b
        del self.c
        del self.d
        del self.wrongtype
        del self.wronglength

    def test_bonds(self):
        dists = MDAnalysis.core.distances.calc_bonds(self.a, self.b)
        assert_equal(len(dists), 4, err_msg="calc_bonds results have wrong length")
        dists_pbc = MDAnalysis.core.distances.calc_bonds(self.a, self.b, box=self.box)
        assert_almost_equal(dists[0], 0.0, self.prec, err_msg="Zero length calc_bonds fail") #tests 0 length
        assert_almost_equal(dists[1], 1.7320508075688772, self.prec, err_msg="Standard length calc_bonds fail") # arbitrary length check
        #PBC checks, 2 without, 2 with
        assert_almost_equal(dists[2], 11.0, self.prec, err_msg="PBC check #1 w/o box") # pbc check 1, subtract single box length
        assert_almost_equal(dists_pbc[2], 1.0, self.prec, err_msg="PBC check #1 with box")
        assert_almost_equal(dists[3], 104.26888318, self.prec, err_msg="PBC check #2 w/o box") # pbc check 2, subtract multiple box lengths in all directions
        assert_almost_equal(dists_pbc[3], 3.46410072, self.prec, err_msg="PBC check #w with box")
        #Bad input checking
        badboxtype = np.array([10., 10., 10.], dtype=np.float64)
        badboxsize = np.array([[10., 10.],[10.,10.,]], dtype=np.float32)
        badresult = np.zeros(len(self.a)-1)
        assert_raises(TypeError, MDAnalysis.core.distances.calc_bonds, self.a, self.wrongtype) # try inputting float64 values
        assert_raises(TypeError, MDAnalysis.core.distances.calc_bonds, self.wrongtype, self.b)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_bonds, self.a, self.wronglength) # try inputting arrays of different length
        assert_raises(ValueError, MDAnalysis.core.distances.calc_bonds, self.wronglength, self.b)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_bonds, self.a, self.b, box=badboxsize) # Bad box data
        assert_raises(TypeError, MDAnalysis.core.distances.calc_bonds, self.a, self.b, box=badboxtype) # Bad box type
        assert_raises(ValueError, MDAnalysis.core.distances.calc_bonds, self.a, self.b, result=badresult) # Bad result array
        
    def test_angles(self):
        angles = MDAnalysis.core.distances.calc_angles(self.a, self.b, self.c)
        # Check calculated values
        assert_equal(len(angles), 4, err_msg="calc_angles results have wrong length")
#        assert_almost_equal(angles[0], 0.0, self.prec, err_msg="Zero length angle calculation failed") # What should this be?
        assert_almost_equal(angles[1], np.pi, self.prec, err_msg="180 degree angle calculation failed")
        assert_almost_equal(np.rad2deg(angles[2]), 90., self.prec, err_msg="Ninety degree angle in calc_angles failed")
        assert_almost_equal(angles[3], 0.098174833, self.prec, err_msg="Small angle failed in calc_angles")
        # Check data type checks
        badresult = np.zeros(len(self.a)-1)       
        assert_raises(TypeError, MDAnalysis.core.distances.calc_angles, self.a, self.wrongtype, self.c) # try inputting float64 values
        assert_raises(TypeError, MDAnalysis.core.distances.calc_angles, self.wrongtype, self.b, self.c)
        assert_raises(TypeError, MDAnalysis.core.distances.calc_angles, self.a, self.b, self.wrongtype)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_angles, self.a, self.wronglength, self.c) # try inputting arrays of different length
        assert_raises(ValueError, MDAnalysis.core.distances.calc_angles, self.wronglength, self.b, self.c)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_angles, self.a, self.b, self.wronglength)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_angles, self.a, self.b, self.c, result=badresult) # Bad result array

    def test_torsions(self):
        torsions = MDAnalysis.core.distances.calc_torsions(self.a, self.b, self.c, self.d)
        # Check calculated values
        assert_equal(len(torsions), 4, err_msg="calc_torsions results have wrong length")
#        assert_almost_equal(torsions[0], 0.0, self.prec, err_msg="Zero length torsion failed")
#        assert_almost_equal(torsions[1], 0.0, self.prec, err_msg="Straight line torsion failed") #All points along a single straight line
        assert_almost_equal(torsions[2], np.pi, self.prec, err_msg="180 degree torsion failed")
        assert_almost_equal(torsions[3], 0.50714064, self.prec, err_msg="arbitrary torsion angle failed") #not sure what this test does that previous doesn't, can't hurt though
        # Check data type checks
        badresult = np.zeros(len(self.a)-1)       
        assert_raises(TypeError, MDAnalysis.core.distances.calc_torsions, self.a, self.wrongtype, self.c, self.d) # try inputting float64 values
        assert_raises(TypeError, MDAnalysis.core.distances.calc_torsions, self.wrongtype, self.b, self.c, self.d)
        assert_raises(TypeError, MDAnalysis.core.distances.calc_torsions, self.a, self.b, self.wrongtype, self.d)
        assert_raises(TypeError, MDAnalysis.core.distances.calc_torsions, self.a, self.b, self.c, self.wrongtype)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_torsions, self.a, self.wronglength, self.c, self.d) # try inputting arrays of different length
        assert_raises(ValueError, MDAnalysis.core.distances.calc_torsions, self.wronglength, self.b, self.c, self.d)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_torsions, self.a, self.b, self.wronglength, self.d)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_torsions, self.a, self.b, self.c, self.wronglength)
        assert_raises(ValueError, MDAnalysis.core.distances.calc_torsions, self.a, self.b, self.c, self.d, result=badresult) # Bad result array      
