"""Numerical checks for the optional offline prototype (numpy + Pillow)."""
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from synthetic_aperture import design, fit, match, points, pyramid, srgb, warp_linear
from refine_aperture import track, track_sequence, aperture_weights, full_coverage_crop, register


class GeometryTests(unittest.TestCase):
    def test_two_depth_scene_keeps_focus_and_preserves_background_parallax(self):
        rng=np.random.default_rng(12)
        background=Image.fromarray(rng.integers(40,210,(240,320),dtype=np.uint8)).filter(ImageFilter.GaussianBlur(.7))
        foreground=Image.fromarray(rng.integers(40,210,(100,100),dtype=np.uint8)).filter(ImageFilter.GaussianBlur(.7))
        frames=[]
        for shift in range(-12,13,4):
            image=Image.new('L',background.size); image.paste(background,(shift//2,0)); image.paste(foreground,(110+shift,70)); frames.append(image.convert('RGB'))
        records,_=register([pyramid(f) for f in frames],(120,80,80,80))
        self.assertEqual(sum('transform' in r for r in records),7)
        total=np.zeros((240,320,3))
        for r,shift in zip(records,range(-12,13,4)):
            np.testing.assert_allclose(r['transform'],[1,0,shift,0],atol=.2)
            warped,_=warp_linear(frames[r['frame']],r['transform']); total+=warped/7
        result=np.asarray(srgb(total),float); ref=np.asarray(frames[3],float)
        self.assertLess(float(np.mean(np.abs(result[90:150,130:190]-ref[90:150,130:190]))),1.)
        self.assertLess(float(result[30:60,40:90].std()),float(ref[30:60,40:90].std())*.65)

    def test_tracking_with_rotation_scale_and_subpixel_shift(self):
        rng=np.random.default_rng(4)
        image=Image.fromarray(rng.integers(0,256,(320,320),dtype=np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
        a,b=1.01,.025; matrix=np.array([[a,-b],[b,a]]); offset=np.array([8.3,-6.7])
        inv=np.linalg.inv(matrix); translation=-inv@offset
        params=(*inv[0],translation[0],*inv[1],translation[1])
        target=image.transform(image.size,Image.Transform.AFFINE,params,resample=Image.Resampling.BICUBIC)
        ref=pyramid(image); p=points(ref[0],(80,80,160,160)); expected=p@matrix.T+offset
        actual,score=track(ref,pyramid(target),p,initial=expected+.5,shape=matrix)
        self.assertLess(float(np.median(np.linalg.norm(actual-expected,axis=1))),.15)
        self.assertGreater(float(np.median(score)),.98)

    def test_adjacent_tracking_handles_total_motion_over_patch_radius(self):
        rng=np.random.default_rng(2)
        image=Image.fromarray(rng.integers(0,256,(240,240),dtype=np.uint8)).filter(ImageFilter.GaussianBlur(1))
        sequence=[]
        for dx in range(-20,21,4):
            shifted=Image.new('L',image.size); shifted.paste(image,(dx,0)); sequence.append(pyramid(shifted))
        p=points(sequence[5][0],(80,80,80,80)); tracked,confidence=track_sequence(sequence,p,5)
        for i,dx in enumerate(range(-20,21,4)):
            self.assertTrue(np.all(confidence[i]>.9))
            np.testing.assert_allclose(tracked[i],p+[dx,0],atol=.1)

    def test_spatial_weights_do_not_overweight_repeated_positions(self):
        w,u,_=aperture_weights([-4,-2,0,2,4],spacing=.1)
        repeated,flat,_=aperture_weights([-4,-2,0,0,0,0,2,4],spacing=.1)
        self.assertAlmostEqual(repeated[2:6].sum(),w[2])
        self.assertAlmostEqual(flat[2:6].sum(),u[2])
        self.assertAlmostEqual(w.sum(),1); self.assertAlmostEqual(u.sum(),1)
        self.assertGreater(w[2],u[2]); self.assertLess(w[0],u[0])
        np.testing.assert_allclose(w,w[::-1])

    def test_common_crop_has_no_incomplete_pixels(self):
        valid=np.ones((50,60),bool); valid[:3]=False; valid[:,-5:]=False
        self.assertEqual(full_coverage_crop(valid),(5,5,55,45))

    def test_robust_fit_rejects_wrong_depth_matches(self):
        rng=np.random.default_rng(5); p=rng.uniform(30,250,(40,2))
        expected=np.array([1.003,.012,17.,-9.])
        q=(design(p)@expected).reshape(-1,2); q[::4]+=35
        actual,quality=fit(p,q,np.ones(len(p)))
        np.testing.assert_allclose(actual,expected,atol=1e-7)
        self.assertEqual(quality['inliers'],30)

    def test_patch_matching_recovers_translation(self):
        rng=np.random.default_rng(7)
        image=Image.fromarray(rng.integers(0,256,(320,320),dtype=np.uint8)).filter(ImageFilter.GaussianBlur(1))
        shifted=Image.new('L',image.size); shifted.paste(image,(13,-7))
        ref=pyramid(image); p=points(ref[0],(100,100,100,100))
        q,score=match(ref,pyramid(shifted),p); coeff,quality=fit(p,q,score)
        np.testing.assert_allclose(coeff,[1,0,13,-7],atol=.15)
        self.assertGreater(quality['inliers'],10)

    def test_warp_direction_and_linear_light(self):
        a=np.zeros((30,40,3),np.uint8); a[10,20]=255
        out,valid=warp_linear(Image.fromarray(a),[1,0,3,2])
        np.testing.assert_allclose(out[8,17],1)
        self.assertFalse(valid[-1,-1])
        self.assertTrue(valid[8,17])
        self.assertEqual(int(np.asarray(srgb(np.ones((1,1,3))*.5))[0,0,0]),188)


if __name__=='__main__': unittest.main()
