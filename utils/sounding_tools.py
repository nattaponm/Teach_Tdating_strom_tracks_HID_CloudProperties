"""
sounding_tools.py — อ่านและวิเคราะห์ข้อมูลตรวจอากาศชั้นบน (radiosonde) ด้วย MetPy
================================================================================

ข้อมูล: สถานีนครราชสีมา (WMO 48431) 00 UTC (07:00 น.) ใน ``data/sounding/``
คอลัมน์: pressure (hPa), height (m), temperature, dewpoint (°C), direction (°), speed (m/s)

ข้อควรระวัง: สถานีอยู่ห่างเรดาร์ขอนแก่นประมาณ 190 km ทางทิศใต้–ตะวันตกเฉียงใต้
และตรวจตอน 07:00 น. ก่อนพายุเกิดหลายชั่วโมง (ไม่มีข้อมูล 12 UTC)
"""

import os

import numpy as np
import pandas as pd


def load_sounding(path):
    """อ่าน CSV → DataFrame ที่เรียงตามความกดอากาศลดลง ไม่มีค่าซ้ำ (เหนือ 100 hPa ตัดทิ้ง)."""
    df = pd.read_csv(path)
    df = df.dropna(subset=["pressure", "height", "temperature", "dewpoint"])
    df = df[df["pressure"] >= 100].drop_duplicates("pressure")
    return df.sort_values("pressure", ascending=False).reset_index(drop=True)


def _units(df, surface_temp=None, surface_dewpoint=None):
    from metpy.units import units
    p = df["pressure"].values * units.hPa
    T = df["temperature"].values.astype(float).copy()
    Td = df["dewpoint"].values.astype(float).copy()
    if surface_temp is not None:
        T[0] = surface_temp
    if surface_dewpoint is not None:
        Td[0] = min(surface_dewpoint, T[0])
    return p, T * units.degC, Td * units.degC


def wind_uv(df):
    """องค์ประกอบลม u (ไปทางตะวันออก), v (ไปทางเหนือ) หน่วย m/s."""
    d = np.radians(df["direction"].values.astype(float))
    s = df["speed"].values.astype(float)
    return -s * np.sin(d), -s * np.cos(d)


def layer_mean_wind(df, p_bottom=850, p_top=300):
    """ลมเฉลี่ยในชั้น (เช่น 850–300 hPa = 'steering wind') → (u, v, speed m/s, ทิศที่ไป °)."""
    m = (df["pressure"] <= p_bottom) & (df["pressure"] >= p_top)
    u, v = wind_uv(df[m])
    um, vm = float(np.mean(u)), float(np.mean(v))
    return um, vm, float(np.hypot(um, vm)), float((np.degrees(np.arctan2(um, vm)) + 360) % 360)


def bulk_shear(df, depth_m=6000):
    """ความแตกต่างของลมระหว่างผิวพื้นกับความสูง depth_m เหนือพื้น (m/s)."""
    z = df["height"].values - df["height"].values[0]
    u, v = wind_uv(df)
    ut, vt = np.interp(depth_m, z, u), np.interp(depth_m, z, v)
    i = 1 if len(u) > 1 else 0          # ระดับผิวพื้นมักรายงานลม 0 → ใช้ระดับถัดไป
    return float(np.hypot(ut - u[i], vt - v[i]))


def isotherm_height(df, temp_c=0.0):
    """ความสูง (m MSL) ที่อุณหภูมิลดลงถึง temp_c เป็นครั้งแรก."""
    t, h = df["temperature"].values, df["height"].values
    idx = np.where((t[:-1] >= temp_c) & (t[1:] < temp_c))[0]
    if not idx.size:
        return np.nan
    i = idx[0]
    return float(h[i] + (temp_c - t[i]) * (h[i + 1] - h[i]) / (t[i + 1] - t[i]))


def compute_params(df, surface_temp=None, surface_dewpoint=None):
    """ดัชนีสำคัญสำหรับพายุฟ้าคะนอง → dict

    surface_temp : แทนอุณหภูมิผิวพื้นด้วยค่านี้ (เช่น 37 °C ตอนบ่าย) เพื่อประมาณสภาพตอนบ่าย
    """
    import metpy.calc as mc
    p, T, Td = _units(df, surface_temp, surface_dewpoint)
    prof = mc.parcel_profile(p, T[0], Td[0])
    cape, cin = mc.cape_cin(p, T, Td, prof)
    lcl_p, _ = mc.lcl(p[0], T[0], Td[0])
    try:
        dcape = mc.downdraft_cape(p, T, Td)[0].m
    except Exception:
        dcape = np.nan
    pw = mc.precipitable_water(p, Td).to("mm").m
    li = mc.lifted_index(p, T, prof).m
    li = float(np.atleast_1d(li)[0])
    u, v, spd, dirto = layer_mean_wind(df)
    t700 = np.interp(700, df["pressure"].values[::-1], df["temperature"].values[::-1])
    t500 = np.interp(500, df["pressure"].values[::-1], df["temperature"].values[::-1])
    z700 = np.interp(700, df["pressure"].values[::-1], df["height"].values[::-1])
    z500 = np.interp(500, df["pressure"].values[::-1], df["height"].values[::-1])
    return {
        "T_sfc_C": float(T[0].m), "Td_sfc_C": float(Td[0].m),
        "SBCAPE_Jkg": float(cape.m), "SBCIN_Jkg": float(cin.m),
        "DCAPE_Jkg": float(dcape), "LCL_hPa": float(lcl_p.m),
        "LI_C": li, "PW_mm": float(pw),
        "K_index": float(mc.k_index(p, T, Td).m),
        "lapse_700_500_Ckm": float((t700 - t500) / ((z500 - z700) / 1000)),
        "freezing_level_m": isotherm_height(df, 0.0),
        "minus20C_level_m": isotherm_height(df, -20.0),
        "shear_0_6km_ms": bulk_shear(df, 6000),
        "steering_speed_ms": spd, "steering_dir_to_deg": dirto,
    }


def plot_skewt(df, fig=None, subplot=111, title=None, surface_temp=None, show_parcel=True,
               show_dcape=False):
    """Skew-T log-p พร้อม parcel, พื้นที่ CAPE/CIN และลม (barb)."""
    import matplotlib.pyplot as plt
    import metpy.calc as mc
    from metpy.plots import SkewT
    from metpy.units import units

    p, T, Td = _units(df, surface_temp)
    fig = fig or plt.figure(figsize=(4.6, 5.0))
    skew = SkewT(fig, subplot=subplot, rotation=45)
    skew.plot(p, T, color="#d62728", lw=1.4, label="Temperature")
    skew.plot(p, Td, color="#2ca02c", lw=1.4, label="Dew point")
    u, v = wind_uv(df)
    step = max(1, len(df) // 25)
    skew.plot_barbs(p[::step], (u[::step] * units("m/s")).to("knots"),
                    (v[::step] * units("m/s")).to("knots"), length=5.5)
    if show_parcel:
        prof = mc.parcel_profile(p, T[0], Td[0]).to("degC")
        skew.plot(p, prof, color="k", lw=1.0, ls="--", label="Surface parcel")
        skew.shade_cape(p, T, prof, alpha=0.25)
        skew.shade_cin(p, T, prof, Td, alpha=0.25)
    if show_dcape:
        try:
            _, dp, dprof = mc.downdraft_cape(p, T, Td)
            skew.plot(dp, dprof.to("degC"), color="#1f77b4", lw=1.0, ls=":", label="Downdraft parcel")
        except Exception:
            pass
    skew.plot_dry_adiabats(lw=0.4, alpha=0.4)
    skew.plot_moist_adiabats(lw=0.4, alpha=0.4)
    skew.plot_mixing_lines(lw=0.4, alpha=0.4)
    skew.ax.axvline(0, color="#1f77b4", lw=0.6, ls="--")
    skew.ax.set_ylim(1000, 150)
    skew.ax.set_xlim(-30, 45)
    skew.ax.set_xlabel("Temperature (°C)")
    skew.ax.set_ylabel("Pressure (hPa)")
    skew.ax.legend(loc="upper left", fontsize=6, frameon=True, framealpha=0.85)
    if title:
        skew.ax.set_title(title, loc="left", fontsize=8)
    return fig, skew


def sounding_files(data_dir):
    d = os.path.join(data_dir, "sounding")
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".csv"))
