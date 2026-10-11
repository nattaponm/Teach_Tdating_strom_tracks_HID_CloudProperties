# Teach_Tdating_strom_tracks_HID_CloudProperties

**สอนวิเคราะห์เส้นทางพายุ (T-DaTing) ร่วมกับขนาดและกายภาพเมฆ ค่าการสะท้อน dual-pol HID Doppler และภูมิประเทศ (DEM)
ผ่านเคสพายุฤดูร้อน 3 พฤษภาคม 2567 — เรดาร์ขอนแก่น (KKN) กรมอุตุนิยมวิทยา**

ชุด notebook สำหรับนิสิตปริญญาตรีปี 3–4 และปริญญาโทด้านวิทยาศาสตร์สิ่งแวดล้อม/ภูมิศาสตร์ เป็นภาษาไทย
มีวัตถุประสงค์ สมการ แผนที่คุณภาพตีพิมพ์ แบบฝึกหัด 3 ข้อพร้อมเฉลยโค้ด คำถามชวนคิด และแนวทางต่อยอดงานวิจัย

> เป็นภาคต่อของ [Teach_Pysteps_KKN_summerStorm](https://github.com/nattaponm/Teach_Pysteps_KKN_summerStorm) (pseudo-CAPPI, nowcasting)
> และ [Teach_HID_Doppler_KKN_summerStorm](https://github.com/nattaponm/Teach_HID_Doppler_KKN_summerStorm) (dealiasing, PyTDA, dual-pol, HID)

## 📚 Notebooks

| # | Notebook | คำถามหลัก | Colab |
|---|---|---|---|
| 00 | [00_prepare_track_dataset](notebooks/00_prepare_track_dataset.ipynb) | (ผู้สอน) รวมข้อมูลทุกชนิดบนกริด 1 km เดียวกัน, สร้างภาพ 5/10 นาที, รัน T-DaTing | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties/blob/main/notebooks/00_prepare_track_dataset.ipynb) |
| 1 | [01_tdating_tracks_multiresolution](notebooks/01_tdating_tracks_multiresolution.ipynb) | เส้นทางพายุที่ 15/10/5 นาทีต่างกันอย่างไร และภาพสังเคราะห์เชื่อได้แค่ไหน | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties/blob/main/notebooks/01_tdating_tracks_multiresolution.ipynb) |
| 2 | [02_track_footprints](notebooks/02_track_footprints.ipynb) | footprint ของเมฆในแต่ละเส้นทาง, IoU ระหว่างความละเอียด, ครอบคลุมจุดรายงาน, ส่งออก GeoPackage | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties/blob/main/notebooks/02_track_footprints.ipynb) |
| 3 | [03_cloud_morphology_kinematics](notebooks/03_cloud_morphology_kinematics.ipynb) | ขนาด centroid ความแรง ความเร็ว ทิศทาง การจำแนกตามอายุ/ขนาด และ boxplot | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties/blob/main/notebooks/03_cloud_morphology_kinematics.ipynb) |
| 4 | [04_dualpol_hid_doppler_along_tracks](notebooks/04_dualpol_hid_doppler_along_tracks.ipynb) | สัดส่วน HID, KDP/ZDR, Doppler (dealiased), divergence, EDR ตามเส้นทาง และวงจรชีวิต | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties/blob/main/notebooks/04_dualpol_hid_doppler_along_tracks.ipynb) |
| 5 | [05_terrain_and_storm_physics](notebooks/05_terrain_and_storm_physics.ipynb) | ภูมิประเทศกับกายภาพเมฆ, จุดก่อตัว, การยกตัวจากความลาด, ตัวแปรแทรกซ้อนจากระยะเรดาร์, สังเคราะห์ | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties/blob/main/notebooks/05_terrain_and_storm_physics.ipynb) |

นิสิตเริ่มที่ NB1 ได้ทันที (ข้อมูลจาก 00 อยู่ใน `data/derived/` แล้ว) — แต่ละ notebook ใช้เวลา 60–90 นาที และรันใน Colab ได้ภายในไม่กี่นาที

## ⚠️ ข้อตกลงสำคัญของการวิเคราะห์
1. **ข้อมูลเรดาร์จริงมีทุก 15 นาที** — ภาพ 5 และ 10 นาทีสร้างด้วย *advection interpolation* (สังเคราะห์) 2 วิธี
   - `linZ`: เฉลี่ยในหน่วย Z เชิงเส้น — เรียบและต่อเนื่อง (**ชุดหลักสำหรับการติดตาม**) แต่แกน ≥ 45 dBZ อ่อนลงมาก
   - `nearest`: เลื่อนภาพจริงที่ใกล้ที่สุด — รักษาความเข้มของแกน แต่รูปร่างกระโดดกลางช่วงทำให้เส้นทางขาดบ่อย
   - ผลทดสอบ leave-one-out: ดีกว่า persistence ที่ 35 dBZ แต่ทำนายแกน ≥ 45 dBZ ไม่ได้ (`data/derived/KKN_20240503_interp_test.csv`)
2. **ค่าความเข้ม HID dual-pol และ Doppler ใช้เฉพาะภาพจริง** (นาที 00/15/30/45) ภาพสังเคราะห์ใช้เพื่อเชื่อมเส้นทางเท่านั้น
3. **หน่วยวิเคราะห์สถิติ = เส้นทาง** (อายุ ≥ 30 นาที) ไม่ใช่เซลล์รายเวลา เพื่อหลีกเลี่ยง pseudo-replication
4. **ระยะจากเรดาร์/ความสูงลำคลื่นเป็นตัวแปรแทรกซ้อน** ของทุกความสัมพันธ์ โดยเฉพาะกับภูมิประเทศ (ภูเขาอยู่ห่างเรดาร์ 90–200 km)

## 🗂️ โครงสร้าง repo
```
data/
├── derived/                                   (สร้างโดย 00; ช่วง 05:00–17:00 UTC, กริด AEQD 1 km 481×481)
│   ├── KKN_20240503_cappi_15min.nc            reflectivity ที่วัดจริง 49 ภาพ
│   ├── KKN_20240503_cappi_05min_{linZ,nearest}.nc   ภาพ 5 นาที (ตัวแปร observed บอกภาพจริง)
│   ├── KKN_20240503_polar_15min.nc            Zc, Vr (dealiased), divergence, az. shear, EDR, KDP, ZDR, HID 4 มุมยก, hail/graupel column
│   ├── KKN_20240503_terrain_1km.nc            elevation, slope, relief, dh/dx, dh/dy, TPI, beam height 0.48°
│   ├── KKN_20240503_labels_{15min,10min_*,05min_*}.nc   ผล T-DaTing (label = track_id + 1)
│   ├── KKN_20240503_interp_test.csv, KKN_20240503_tracking_summary.csv, manifest.json
├── basemap/   reports/   sounding/
utils/
├── track_tools.py      ฟังก์ชันหลักของ repo นี้ (แทรกภาพ, T-DaTing, footprint, คุณสมบัติเซลล์/เส้นทาง, สถิติ, แผนที่)
├── polar_tools.py      จาก repo HID/Doppler (ใช้ใน 00)
├── mapplot.py, kkn_tools.py, data_io.py, sounding_tools.py   จาก repo pysteps
notebooks/   00–05
```

### พารามิเตอร์ T-DaTing (เหมือนกันทุกความละเอียด)
`minref=33, maxref=45, mindiff=5, minsize=15, minmax=40, mindis=8, mintrack=2, match_frac=0.25`

## ▶️ การใช้งาน
**Google Colab (แนะนำ):** กด *Open in Colab* แล้วรันเซลล์ ⚙️ Setup ก่อน (ติดตั้ง pysteps, Py-ART ฯลฯ และ clone repo)

**เครื่องตัวเอง:**
```bash
git clone https://github.com/nattaponm/Teach_Tdating_strom_tracks_HID_CloudProperties.git
cd Teach_Tdating_strom_tracks_HID_CloudProperties
pip install -r requirements.txt
# ถ้าจะรัน 00 ใหม่: pip install --no-build-isolation git+https://github.com/nasa/PyTDA.git
jupyter lab
```

## 🙏 แหล่งข้อมูลและการอ้างอิง
- ข้อมูลเรดาร์: **กรมอุตุนิยมวิทยา (TMD)** — ใช้เพื่อการศึกษา
- DEM: AWS Terrain Tiles (SRTM/GMTED2010); ขอบเขตการปกครอง: geoBoundaries (CC BY 4.0)
- Sounding: University of Wyoming (48431); รายงานความเสียหาย: ปภ. และสื่อมวลชน (`data/reports/README.md`)
- ซอฟต์แวร์: pysteps (Pulkkinen et al., 2019), Py-ART (Helmus & Collis, 2016), PyTDA, cartopy, geopandas, rasterio
