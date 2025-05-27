# 🚀 Example Run for DefoEye

This guide demonstrates how to run the current partial release of the **DefoEye** software using a test dataset.

---

## 🧪 Test Dataset

The test dataset includes 8 Sentinel-1 SAR scenes (Descending mode, Subswath12, Path 143, Frame 492) related to a **Houston** case study.
The released code already supports until the end of Phase Unwrapping stage.

📦 A sample dataset can be downloaded from:
> 📦 **[Download from Zenodo](https://doi.org/10.5281/zenodo.15525706)**  
> This dataset is for evaluating the partial release of the DefoEye software.
---

## 🔧 Run Command

Run the software with the following command:

```bash
python main.py \
  --base_path /path/to/DefoEye/Test_dataset/ \
  --work_path /path/to/DefoEye/DefoEye_Outputs/ \
  --IW_number 1 2 \
  --temporal_baseline 36 \
  --spatial_baseline 250 \
  --filter_intf_pairs True \
  --TH_number_of_connections 4 \
  --filter_wavelength_value 200 \
  --range_dec_value 20 \
  --azimuth_dec_value 5 \
  --n_jobs_for_intf 10 \
  --n_jobs_for_merging 10 \
  --n_jobs_for_unwrapping 5

