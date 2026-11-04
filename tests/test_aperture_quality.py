import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from aperture_quality import capped_weights,spatial_weights,recommend
class QualityTests(unittest.TestCase):
 def test_cap_preserves_normalization(self):
  w=capped_weights([100]+[1]*19);self.assertAlmostEqual(w.sum(),1);self.assertLessEqual(w.max(),.12000001)
 def test_ring_does_not_count_as_filled_area(self):
  t=np.linspace(0,2*np.pi,64,endpoint=False);p=np.column_stack((20*np.cos(t),20*np.sin(t)))
  with self.assertRaises(ValueError):spatial_weights(p,1,1,True)
 def test_filled_grid_has_coverage_and_bounded_group_weights(self):
  y,x=np.mgrid[-20:21:4,-20:21:4];p=np.column_stack((x.ravel(),y.ravel()));w,r=spatial_weights(p,1,1,True)
  self.assertGreater(r['coverageFraction'],.9);self.assertLessEqual(r['maxGroupWeight'],.12000001);self.assertAlmostEqual(w.sum(),1)
  self.assertGreater(recommend(p,1,True)['apertureFraction'],.5)
 def test_sparse_dominant_samples_are_rejected(self):
  p=np.array([[0,0],[1,0],[2,0],[30,30],[30,-30],[-30,30],[-30,-30]])
  with self.assertRaises(ValueError):spatial_weights(p,1,1,True)
if __name__=='__main__':unittest.main()
