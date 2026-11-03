import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from lab_engine import spatial_weights

class PupilTests(unittest.TestCase):
    def test_repeated_positions_share_same_pupil_area(self):
        p=np.column_stack((np.linspace(-20,20,21),np.zeros(21)))
        base,_=spatial_weights(p)
        repeated=np.vstack([p,p[10],p[10],p[10]])
        w,_=spatial_weights(repeated)
        self.assertAlmostEqual(base[10],w[10]+w[21:].sum(),places=6)
        self.assertAlmostEqual(w.sum(),1)

    def test_smaller_aperture_rejects_outer_positions(self):
        p=np.column_stack((np.linspace(-20,20,41),np.zeros(41)))
        w,info=spatial_weights(p,.5,0)
        self.assertTrue(np.all(w[np.abs(p[:,0])>10]==0))
        self.assertLess(info['usedFrames'],len(p));self.assertAlmostEqual(w.sum(),1)

    def test_two_dimensional_pupil_is_rotationally_symmetric(self):
        y,x=np.mgrid[-20:21:5,-20:21:5];p=np.column_stack((x.ravel(),y.ravel()))
        w,info=spatial_weights(p,1,1,True)
        self.assertEqual(info['kind'],'area');self.assertAlmostEqual(w.sum(),1)
        self.assertTrue(np.all(w[np.linalg.norm(p,axis=1)>20]==0))
        np.testing.assert_allclose(w.reshape(9,9),np.rot90(w.reshape(9,9)),atol=.003)

    def test_line_is_not_reported_as_area_and_invalid_inputs_fail(self):
        p=np.column_stack((np.linspace(-20,20,21),np.zeros(21)))
        with self.assertRaisesRegex(ValueError,'zu schmal'):spatial_weights(p,1,1,True)
        for aperture in (0,2,float('nan')):
            with self.assertRaises(ValueError):spatial_weights(p,aperture)
        with self.assertRaises(ValueError):spatial_weights(np.zeros((8,2)))

if __name__=='__main__':unittest.main()
