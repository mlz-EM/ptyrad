import numpy as np
from scipy.ndimage import affine_transform
from scipy.optimize import least_squares
from skimage.registration import phase_cross_correlation
import matplotlib.pyplot as plt
import tifffile

## -40 deg rotation means object rotate 40 deg clock wise will match the ground truth

def plot_alignment(aligned: np.ndarray, ground: np.ndarray, outpath='aligned.png'):
    fig, axes = plt.subplots(1,1,figsize=(4,4))
    axes.imshow(ground, cmap='gray')
    axes.imshow(aligned, cmap='inferno', alpha=0.3)
    axes.axis('off')
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close(fig)

def compose_affine(scale, rot_deg, dy, dx, center):
    theta = np.deg2rad(rot_deg)
    R = scale * np.array([
        [ np.cos(theta), -np.sin(theta)],
        [ np.sin(theta),  np.cos(theta)]
    ])
    t = center - R @ center + [dy, dx]
    M = np.eye(3)
    M[:2, :2] = R
    M[:2, 2]  = t
    return M

def warp_with_matrix(img, M, shape_out):
    Ainv = np.linalg.inv(M[:2,:2])
    offset = -Ainv @ M[:2,2]
    return affine_transform(
        img.astype(float),
        matrix=Ainv, offset=offset,
        output_shape=shape_out,
        order=1, mode='constant', cval=np.nan
    )

def normalize_within_mask(img, mask):
    vals = img[mask]
    return (img - np.nanmean(vals)) / (np.nanstd(vals) + 1e-6)


def align_object_to_ground_truth(
    object_mean, object_sampling,
    ground_truth_path='ground_truth.tif', refinement_niter=1
):
    with tifffile.TiffFile(ground_truth_path) as f:
        ground_truth = f.asarray().astype(float)
        ground_truth_sampling = float(f.shaped_metadata[0]['spacing'])
        rotation_angle = float(f.shaped_metadata[0]['rotation'])

    H_out, W_out = ground_truth.shape
    H_in,  W_in  = object_mean.shape

    center_in  = np.array([H_in / 2, W_in / 2])
    center_out = np.array([H_out / 2, W_out / 2])
    scale1 = object_sampling / ground_truth_sampling

    # Coarse transform: scale -> shift -> rotate
    M_zoom  = compose_affine(scale1, 0.0, 0.0, 0.0, center_in)
    mapped_center = M_zoom @ np.r_[center_in, 1]
    shift = center_out - mapped_center[:2]
    M_shift = compose_affine(1.0, 0.0, *shift, center_out)
    M_rot   = compose_affine(1.0, rotation_angle, 0.0, 0.0, center_out)
    M1a = M_rot @ M_shift @ M_zoom

    # Initial warp and mask
    obj1   = warp_with_matrix(object_mean, M1a, (H_out, W_out))
    mask1  = warp_with_matrix(np.ones_like(object_mean), M1a, (H_out, W_out)) > 0.5

    # Align by translation
    dy, dx  = phase_cross_correlation(
        ground_truth, obj1,
        reference_mask=mask1, moving_mask=mask1,
        upsample_factor=1, overlap_ratio=0.9
    )
    M1t = compose_affine(1.0, 0.0, dy, dx, center_out)
    M1  = M1t @ M1a

    # Refinement
    x0 = np.array([1.0, 0.0, 0.0, 0.0])
    max_t = 2.0 / ground_truth_sampling
    bounds = ([0.95, -5, -max_t, -max_t],
              [1.05,  5,  max_t,  max_t])

    def residuals(p):
        M2 = compose_affine(*p, center=center_out)
        Mtot = M2 @ M1
        warped = warp_with_matrix(object_mean, Mtot, (H_out, W_out))
        mask   = warp_with_matrix(np.ones_like(object_mean), Mtot, (H_out, W_out)) > 0.5
        if not mask.any(): return np.zeros(1)
        warped_n  = normalize_within_mask(warped, mask)
        target_n  = normalize_within_mask(ground_truth, mask)
        return  np.sqrt(np.mean((warped_n[mask] - target_n[mask])**2))

    res = least_squares(residuals, x0, bounds=bounds, method='dogbox', max_nfev=refinement_niter)

    M2   = compose_affine(*res.x, center=center_out)
    Mtot = M2 @ M1
    obj_final = warp_with_matrix(object_mean, Mtot, (H_out, W_out))

    # Final error (intensity invariant)
    mask = warp_with_matrix(np.ones_like(object_mean), Mtot, (H_out, W_out)) > 0.5
    obj_n = normalize_within_mask(obj_final, mask)
    tgt_n = normalize_within_mask(ground_truth, mask)
    rmse  = np.sqrt(np.mean((obj_n[mask] - tgt_n[mask])**2))

    plot_alignment(obj_final, ground_truth, )
    
    return obj_final, ground_truth, rmse
