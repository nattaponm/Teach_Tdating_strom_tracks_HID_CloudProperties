"""
mapplot.py — แผนที่เรดาร์คุณภาพระดับตีพิมพ์ สำหรับเรดาร์ขอนแก่น (KKN)
=====================================================================

* projection = Azimuthal Equidistant ที่มีเรดาร์เป็นศูนย์กลาง (วงระยะเป็นวงกลมจริง)
* ขอบเขตประเทศ/จังหวัด/อำเภอ และภูมิประเทศ อ่านจาก ``data/basemap`` (ไม่ต้องดาวน์โหลด)
* วงระยะ 60/120/180/240 km, scale bar, ลูกศรทิศเหนือ, ป้าย (a), (b), ...
* จุดรายงานความเสียหาย (ลมกระโชก/ลูกเห็บ) จาก ``data/reports``
* บันทึกรูป PNG 300 dpi + PDF (vector) ลงโฟลเดอร์ ``figures/``

ตัวอย่าง
--------
>>> mp.set_data_dir(DATA)
>>> fig, axs = mp.map_panels(1, 2, meta)
>>> im = mp.radar_map(axs[0], Z[i], meta, title="Observed")
>>> mp.add_colorbar(fig, im, axs)
>>> mp.save_figure(fig, "fig01_example")
"""

import os
import string
import datetime as _dt

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np

import cartopy.crs as ccrs

FIG_DIR = "figures"
DATA_DIR = "data"
LOCAL_OFFSET_H = 7
RANGE_RINGS_KM = (60, 120, 180, 240)

# ค่าตั้งต้นของ basemap (แก้จาก notebook ได้ เช่น mp.BASEMAP["districts"] = False)
BASEMAP = {"districts": True, "provinces": True, "province_labels": False, "rings": True}
POINTS = []                     # จุดอ้างอิง: list ของ (ชื่อ, lon, lat, marker[, (dx, dy)])

_LAYERS = {}


def set_data_dir(path):
    global DATA_DIR
    DATA_DIR = path
    _LAYERS.clear()


# ---------------------------------------------------------------------------
# 1) สไตล์
# ---------------------------------------------------------------------------
def set_style(base_fontsize=9):
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": base_fontsize, "axes.titlesize": base_fontsize + 1,
        "axes.labelsize": base_fontsize, "xtick.labelsize": base_fontsize - 1,
        "ytick.labelsize": base_fontsize - 1, "legend.fontsize": base_fontsize - 1,
        "axes.linewidth": 0.8, "lines.linewidth": 1.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "grid.linewidth": 0.4, "grid.alpha": 0.5,
        "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def halo(w=1.6):
    return [pe.withStroke(linewidth=w, foreground="white")]


# ---------------------------------------------------------------------------
# 2) projection และ panel
# ---------------------------------------------------------------------------
def get_crs(meta):
    return ccrs.AzimuthalEquidistant(central_longitude=meta["radar_lon"],
                                     central_latitude=meta["radar_lat"])


def extent_of(meta):
    return (meta["x1"], meta["x2"], meta["y1"], meta["y2"])


def map_panels(nrows, ncols, meta, panel_width=3.2, extra_height=0.0, zoom=None):
    """figure ที่ทุก panel ใช้ projection ของข้อมูล — คืนค่า (fig, axs 1 มิติ)."""
    ext = zoom or extent_of(meta)
    aspect = (ext[3] - ext[2]) / (ext[1] - ext[0])
    fig, axs = plt.subplots(nrows, ncols,
                            figsize=(panel_width * ncols, panel_width * aspect * nrows + 0.6 + extra_height),
                            subplot_kw={"projection": get_crs(meta)}, squeeze=False,
                            layout="constrained")
    return fig, axs.ravel()


# ---------------------------------------------------------------------------
# 3) ชั้นข้อมูลพื้นหลัง
# ---------------------------------------------------------------------------
def _layers(meta):
    key = meta["projection"]
    if key in _LAYERS:
        return _LAYERS[key]
    import geopandas as gpd
    L = {}
    gpkg = os.path.join(DATA_DIR, "basemap", "boundaries_KKN_255km.gpkg")
    for lyr, tol in (("adm0", 100.0), ("adm1", 150.0), ("adm2", 250.0)):
        try:
            g = gpd.read_file(gpkg, layer=lyr).to_crs(meta["projection"])
            g["geometry"] = g.geometry.simplify(tol, preserve_topology=True)
            L[lyr] = g
        except Exception:
            L[lyr] = None
    _LAYERS[key] = L
    return L


def add_basemap(ax, meta, gridlines=True, labels=("left", "bottom"), districts=None,
                provinces=None, province_labels=None, rings=None):
    """ขอบเขตอำเภอ (บาง), จังหวัด, ประเทศ (มี halo), วงระยะ, ตำแหน่งเรดาร์ และเส้นกริด lon/lat."""
    districts = BASEMAP["districts"] if districts is None else districts
    provinces = BASEMAP["provinces"] if provinces is None else provinces
    province_labels = BASEMAP["province_labels"] if province_labels is None else province_labels
    rings = BASEMAP["rings"] if rings is None else rings
    L, crs = _layers(meta), get_crs(meta)
    if districts and L.get("adm2") is not None:
        ax.add_geometries(L["adm2"].geometry, crs=crs, facecolor="none", edgecolor="0.6",
                          linewidth=0.2, alpha=0.7, zorder=3)
    if provinces and L.get("adm1") is not None:
        ax.add_geometries(L["adm1"].geometry, crs=crs, facecolor="none", edgecolor="0.3",
                          linewidth=0.5, zorder=3.2)
    if L.get("adm0") is not None:
        ax.add_geometries(L["adm0"].geometry, crs=crs, facecolor="none", edgecolor="white",
                          linewidth=1.8, zorder=3.3)
        ax.add_geometries(L["adm0"].geometry, crs=crs, facecolor="none", edgecolor="black",
                          linewidth=0.8, zorder=3.4)
    if province_labels:
        add_province_labels(ax, meta)
    if rings:
        add_range_rings(ax, meta)
    ax.plot(0, 0, marker="^", ms=5, mfc="k", mec="w", mew=0.6, transform=crs, zorder=8)
    if gridlines:
        import matplotlib.ticker as mticker
        from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
        gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.3, color="0.45",
                          alpha=0.5, linestyle=":", x_inline=False, y_inline=False,
                          rotate_labels=False, zorder=4)
        gl.top_labels = "top" in labels
        gl.right_labels = "right" in labels
        gl.left_labels = "left" in labels
        gl.bottom_labels = "bottom" in labels
        lon0, lon1, lat0, lat1 = ax.get_extent(ccrs.PlateCarree())
        span = max(lon1 - lon0, lat1 - lat0)
        steps = np.array([0.1, 0.2, 0.25, 0.5, 1, 2])
        step = steps[np.argmin(np.abs(span / steps - 4))]
        gl.xlocator = mticker.MultipleLocator(step)
        gl.ylocator = mticker.MultipleLocator(step)
        gl.xformatter, gl.yformatter = LongitudeFormatter(), LatitudeFormatter()
        gl.xlabel_style = {"size": mpl.rcParams["xtick.labelsize"] - 1, "color": "0.2"}
        gl.ylabel_style = {"size": mpl.rcParams["ytick.labelsize"] - 1, "color": "0.2"}
    return ax


def add_province_labels(ax, meta, fontsize=5.5, min_sep_km=28):
    L, crs = _layers(meta), get_crs(meta)
    g = L.get("adm1")
    if g is None:
        return
    x0, x1, y0, y1 = ax.get_extent(crs)
    th = g[g["iso"] == "THA"].copy()
    th["area"] = th.geometry.area
    placed = []
    for _, row in th.sort_values("area", ascending=False).iterrows():
        p = row.geometry.representative_point()
        if not (x0 < p.x < x1 and y0 < p.y < y1) or row["area"] < 8e8:
            continue
        if any(np.hypot(p.x - a, p.y - b) < min_sep_km * 1e3 for a, b in placed):
            continue
        ax.text(p.x, p.y, row["name"], transform=crs, fontsize=fontsize, color="0.2",
                ha="center", va="center", path_effects=halo(1.4), zorder=6)
        placed.append((p.x, p.y))


def add_range_rings(ax, meta, radii_km=None, color="0.25", label=True, label_az=40):
    crs = get_crs(meta)
    x0, x1, y0, y1 = ax.get_extent(crs)
    th = np.linspace(0, 2 * np.pi, 361)
    for r in radii_km or RANGE_RINGS_KM:
        last = r == max(radii_km or RANGE_RINGS_KM)
        ax.plot(r * 1e3 * np.sin(th), r * 1e3 * np.cos(th), color=color,
                lw=0.6 if last else 0.4, ls="-" if last else (0, (3, 2)), transform=crs, zorder=4)
        a = np.radians(label_az)
        lx, ly = r * 1e3 * np.sin(a), r * 1e3 * np.cos(a)
        if label and x0 < lx < x1 and y0 < ly < y1:
            ax.text(lx, ly, f"{r} km", transform=crs, fontsize=5.5, color="0.15",
                    ha="center", va="center", path_effects=halo(1.4), zorder=6)


def add_terrain(ax, meta, alpha=1.0, vmax=1400):
    """ภูมิประเทศแบบ hillshade (จาก data/basemap/terrain_KKN_aeqd_600m.nc)."""
    import xarray as xr
    from matplotlib.colors import LightSource, LinearSegmentedColormap, PowerNorm
    with xr.open_dataset(os.path.join(DATA_DIR, "basemap", "terrain_KKN_aeqd_600m.nc")) as ds:
        x, y, z = ds["x"].values, ds["y"].values, ds["elevation"].values.astype(float)
    cmap = LinearSegmentedColormap.from_list("hypso", [
        (0, "#e9efe0"), (0.1, "#d6e3c3"), (0.22, "#c9d8a8"), (0.4, "#e2d6a8"),
        (0.62, "#cdb48d"), (0.82, "#a98c74"), (1, "#8a7a70")])
    norm = PowerNorm(0.55, vmin=0, vmax=vmax)
    dx = float(np.median(np.diff(x)))
    rgb = LightSource(azdeg=315, altdeg=40).shade(np.nan_to_num(z), cmap=cmap, norm=norm,
                                                   blend_mode="soft", vert_exag=2.5, dx=dx, dy=dx)
    ax.imshow(rgb, origin="lower", transform=get_crs(meta), alpha=alpha, zorder=1,
              extent=[x[0] - dx / 2, x[-1] + dx / 2, y[0] - dx / 2, y[-1] + dx / 2],
              interpolation="bilinear", rasterized=True)
    return mpl.cm.ScalarMappable(norm=norm, cmap=cmap)


def terrain_at(meta, lon, lat):
    """ความสูงภูมิประเทศ (m) ที่ lon/lat."""
    import xarray as xr
    from pyproj import Transformer
    xx, yy = Transformer.from_crs("EPSG:4326", meta["projection"], always_xy=True).transform(lon, lat)
    xx, yy = np.atleast_1d(xx), np.atleast_1d(yy)
    with xr.open_dataset(os.path.join(DATA_DIR, "basemap", "terrain_KKN_aeqd_600m.nc")) as ds:
        v = ds["elevation"].astype(float).interp(x=xr.DataArray(xx, dims="p"),
                                                 y=xr.DataArray(yy, dims="p")).values
    return v if v.size > 1 else float(v[0])


def add_points(ax, meta, points=None, fontsize=None, color="k"):
    """จุดอ้างอิง list ของ (ชื่อ, lon, lat, marker[, (dx, dy) point])."""
    points = POINTS if points is None else points
    fs = fontsize or mpl.rcParams["font.size"] - 2
    pc = ccrs.PlateCarree()
    x0, x1, y0, y1 = ax.get_extent(pc)
    for pt in points:
        name, lon, lat, marker = pt[:4]
        off = pt[4] if len(pt) > 4 else (4, 3)
        if not (x0 <= lon <= x1 and y0 <= lat <= y1):
            continue
        ax.plot(lon, lat, marker=marker, ms=5, mfc="w", mec=color, mew=1.0, transform=pc, zorder=9)
        if name:
            ax.annotate(name, xy=(lon, lat), xycoords=pc._as_mpl_transform(ax), xytext=off,
                        textcoords="offset points", fontsize=fs, zorder=9, color=color,
                        ha="left" if off[0] >= 0 else "right",
                        va="bottom" if off[1] >= 0 else "top", path_effects=halo(1.5))


REPORT_STYLE = {   # hazard → (marker, สี, label)
    "hail": ("D", "#7b3294", "Wind + hail"),
    "wind": ("X", "#d7191c", "Damaging wind"),
}


def add_reports(ax, reports, label_col=None, fontsize=5.5, legend=True, ms=5):
    """จุดรายงานความเสียหาย: ◆ = ลมกระโชก + ลูกเห็บ, ✕ = ลมแรง (ขอบดำ = เวลาแน่นอน/โดยประมาณ, ขอบเทา = กลางคืน)."""
    pc = ccrs.PlateCarree()
    handles = {}
    lo0, lo1, la0, la1 = ax.get_extent(pc)
    for _, r in reports.iterrows():
        if not (lo0 <= r["lon"] <= lo1 and la0 <= r["lat"] <= la1):
            continue
        kind = "hail" if "ลูกเห็บ" in str(r["hazard"]) else "wind"
        mk, col, lab = REPORT_STYLE[kind]
        night = r.get("time_quality") == "night"
        h, = ax.plot(r["lon"], r["lat"], marker=mk, ms=ms, mfc=col, mec="0.5" if night else "k",
                     mew=0.6, ls="none", transform=pc, zorder=10)
        handles[lab] = h
        if label_col:
            ax.annotate(str(r[label_col]), xy=(r["lon"], r["lat"]), xycoords=pc._as_mpl_transform(ax),
                        xytext=(3, 3), textcoords="offset points", fontsize=fontsize, zorder=10,
                        path_effects=halo(1.4))
    if legend and handles:
        ax.legend(list(handles.values()), list(handles.keys()), loc="lower left",
                  fontsize=6, frameon=True, framealpha=0.85, handletextpad=0.3, borderpad=0.3)


def add_scalebar(ax, length_km=None, location=(0.62, 0.05), linewidth=3):
    x0, x1, y0, y1 = ax.get_extent(ax.projection)
    width_km = (x1 - x0) / 1000.0
    if length_km is None:
        cand = np.array([10, 20, 25, 50, 100, 150, 200])
        length_km = cand[np.argmin(np.abs(cand - width_km / 5))]
    bx, by = x0 + location[0] * (x1 - x0), y0 + location[1] * (y1 - y0)
    L = length_km * 1000.0
    kw = dict(transform=ax.projection, zorder=9, solid_capstyle="butt")
    ax.plot([bx, bx + L], [by, by], color="k", linewidth=linewidth, **kw)
    ax.plot([bx, bx + L / 2], [by, by], color="w", linewidth=linewidth - 1.6, **kw)
    ax.text(bx + L / 2, by + 0.015 * (y1 - y0), f"{length_km:g} km", ha="center", va="bottom",
            fontsize=mpl.rcParams["font.size"] - 2, transform=ax.projection, zorder=9,
            path_effects=halo(1.4))


def add_north_arrow(ax, xy=(0.95, 0.88), length_pt=16):
    ax.annotate("", xy=xy, xycoords="axes fraction", xytext=(0, -length_pt),
                textcoords="offset points",
                arrowprops=dict(arrowstyle="-|>,head_width=0.25,head_length=0.5", color="k", lw=1.2),
                zorder=9)
    ax.annotate("N", xy=xy, xycoords="axes fraction", xytext=(0, 2), textcoords="offset points",
                ha="center", va="bottom", fontsize=mpl.rcParams["font.size"] - 1,
                fontweight="bold", zorder=9)


def add_panel_label(ax, label, loc="upper left"):
    x, ha = (0.02, "left") if "left" in loc else (0.98, "right")
    y, va = (0.98, "top") if "upper" in loc else (0.02, "bottom")
    ax.text(x, y, label, transform=ax.transAxes, ha=ha, va=va,
            fontsize=mpl.rcParams["font.size"] + 1, fontweight="bold", zorder=11,
            bbox=dict(boxstyle="round,pad=0.2", fc="w", ec="0.6", lw=0.5, alpha=0.9))


def panel_labels(axs, start=0):
    for i, ax in enumerate(np.ravel(axs)):
        add_panel_label(ax, f"({string.ascii_lowercase[start + i]})")


def corner_text(ax, txt, loc="upper right", fontsize=None):
    pos = {"upper right": (0.98, 0.98, "right", "top"), "lower right": (0.98, 0.02, "right", "bottom"),
           "upper left": (0.02, 0.98, "left", "top")}[loc]
    ax.text(pos[0], pos[1], txt, transform=ax.transAxes, ha=pos[2], va=pos[3],
            fontsize=fontsize or mpl.rcParams["font.size"] - 2, zorder=11,
            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none", alpha=0.85))


# ---------------------------------------------------------------------------
# 4) colormap
# ---------------------------------------------------------------------------
REFL_LEVELS = np.arange(0, 75, 5)


def refl_cmap_norm(levels=REFL_LEVELS):
    """colormap reflectivity แบบไม่ต่อเนื่องทุก 5 dBZ (ChaseSpectral; คนตาบอดสีอ่านได้)."""
    try:
        import cmweather  # noqa: F401
        base = mpl.colormaps["ChaseSpectral"]
    except Exception:
        base = mpl.colormaps["turbo"]
    pos = (np.asarray(levels[:-1]) + 2.5 + 10) / 90.0
    cmap = mpl.colors.ListedColormap(base(np.clip(pos, 0, 1)))
    cmap.set_over(base(min(1.0, (levels[-1] + 12.5) / 90)))
    cmap.set_bad((0, 0, 0, 0))
    return cmap, mpl.colors.BoundaryNorm(levels, cmap.N)


RAIN_LEVELS = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 50, 75, 100, 150]
DEPTH_LEVELS = [1, 2, 5, 10, 15, 20, 30, 40, 50, 75, 100, 150]


def rain_cmap_norm(levels=RAIN_LEVELS):
    base = mpl.colormaps["viridis_r"]
    cmap = mpl.colors.ListedColormap(base(np.linspace(0.05, 0.95, len(levels) - 1)))
    cmap.set_over(base(1.0))
    cmap.set_bad((0, 0, 0, 0))
    return cmap, mpl.colors.BoundaryNorm(levels, cmap.N)


# ---------------------------------------------------------------------------
# 5) แผนที่
# ---------------------------------------------------------------------------
def _edges(meta):
    x, y = meta["x"], meta["y"]
    d = meta["xpixelsize"] / 2
    return np.append(x - d, x[-1] + d), np.append(y - np.sign(y[1] - y[0]) * d,
                                                  y[-1] + np.sign(y[1] - y[0]) * d)


def _setup(ax, meta, zoom, nodata_color, show_coverage=True):
    crs = get_crs(meta)
    ax.set_extent(zoom or extent_of(meta), crs=crs)
    ax.set_facecolor(nodata_color)
    if show_coverage:
        xe, ye = _edges(meta)
        cov = np.where(meta["coverage"], 1.0, np.nan)
        ax.pcolormesh(xe, ye, cov, cmap=mpl.colors.ListedColormap(["#f4f4f4"]), transform=crs,
                      zorder=1, rasterized=True)
    return crs


def radar_map(ax, field, meta, units="dBZ", ptype="intensity", title=None, zoom=None,
              basemap=True, scalebar=True, north=True, nodata_color="white",
              gridline_labels=("left", "bottom"), points=True, probthr=None, min_value=None):
    """แผนที่ reflectivity (dBZ), อัตราฝน (mm/h), ฝนสะสม (mm) หรือความน่าจะเป็น (0–1)

    พื้นเทาอ่อน = อยู่ในรัศมีเรดาร์แต่ไม่มี echo,  สีขาว = นอกรัศมี (ไม่มีข้อมูล)
    คืนค่า artist สำหรับ add_colorbar
    """
    crs = _setup(ax, meta, zoom, nodata_color)
    xe, ye = _edges(meta)
    f = np.asarray(field, float)
    if ptype == "prob":
        cmap = mpl.colormaps["OrRd"].copy()
        levels = np.linspace(0, 1, 11)
        norm = mpl.colors.BoundaryNorm(levels, cmap.N)
        data = np.ma.masked_where(~np.isfinite(f) | (f < 0.05), f)
        label = f"Probability (> {probthr})" if probthr else "Probability"
        ticks = levels
    elif units == "dBZ":
        cmap, norm = refl_cmap_norm()
        thr = REFL_LEVELS[0] if min_value is None else min_value
        data = np.ma.masked_where(~np.isfinite(f) | (f < thr), f)
        label, ticks = "Reflectivity $Z_H$ (dBZ)", REFL_LEVELS[::2]
    else:
        levels = DEPTH_LEVELS if ptype == "depth" else RAIN_LEVELS
        cmap, norm = rain_cmap_norm(levels)
        data = np.ma.masked_where(~np.isfinite(f) | (f < levels[0]), f)
        label = "Rainfall (mm)" if ptype == "depth" else "Rain rate (mm h$^{-1}$)"
        ticks = levels
    im = ax.pcolormesh(xe, ye, data, cmap=cmap, norm=norm, transform=crs, zorder=2,
                       rasterized=True)
    im._label, im._ticks = label, ticks
    if basemap:
        add_basemap(ax, meta, labels=gridline_labels)
    if points:
        add_points(ax, meta)
    if scalebar:
        add_scalebar(ax)
    if north:
        add_north_arrow(ax)
    if title:
        ax.set_title(title, loc="left", fontsize=mpl.rcParams["axes.titlesize"] - 1)
    return im


def field_map(ax, field, meta, cmap="RdBu_r", levels=None, vmin=None, vmax=None, label="",
              title=None, zoom=None, basemap=True, scalebar=True, north=False,
              gridline_labels=("left", "bottom"), points=True, extend="both"):
    """แผนที่ตัวแปรทั่วไป (เช่น ผลต่าง, ความถี่, ความสูง) — ใส่ levels เพื่อใช้สีแบบไม่ต่อเนื่อง."""
    crs = _setup(ax, meta, zoom, "white")
    xe, ye = _edges(meta)
    cm = mpl.colormaps[cmap] if isinstance(cmap, str) else cmap
    norm = mpl.colors.BoundaryNorm(levels, cm.N, extend=extend) if levels is not None else None
    im = ax.pcolormesh(xe, ye, np.ma.masked_invalid(field), cmap=cm, norm=norm,
                       vmin=None if norm else vmin, vmax=None if norm else vmax,
                       transform=crs, zorder=2, rasterized=True)
    im._label, im._ticks = label, levels
    if basemap:
        add_basemap(ax, meta, labels=gridline_labels)
    if points:
        add_points(ax, meta)
    if scalebar:
        add_scalebar(ax)
    if north:
        add_north_arrow(ax)
    if title:
        ax.set_title(title, loc="left", fontsize=mpl.rcParams["axes.titlesize"] - 1)
    return im


def obs_contour(ax, field, meta, level=35.0, color="k", linewidth=0.7, label=None):
    """เส้น contour ของค่าสังเกต (เช่น 35 dBZ) ทับบนแผนที่."""
    cs = ax.contour(meta["x"], meta["y"], np.nan_to_num(field, nan=-99), levels=[level],
                    colors=color, linewidths=linewidth, transform=get_crs(meta), zorder=5)
    if label:
        from matplotlib.lines import Line2D
        ax.legend(handles=[Line2D([], [], color=color, lw=linewidth, label=label)],
                  loc="lower right", frameon=True, framealpha=0.8, fontsize=6)
    return cs


def add_colorbar(fig, im, axs, orientation="horizontal", label=None, shrink=0.6, pad=0.02,
                 aspect=40, extend=None, ticks=None):
    cb = fig.colorbar(im, ax=list(np.ravel(axs)), orientation=orientation, shrink=shrink,
                      pad=pad, aspect=aspect, extend=extend or "max",
                      ticks=ticks if ticks is not None else getattr(im, "_ticks", None))
    cb.formatter = mpl.ticker.FuncFormatter(lambda v, p: f"{v:g}")
    cb.update_ticks()
    cb.set_label(label or getattr(im, "_label", ""))
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(labelsize=mpl.rcParams["xtick.labelsize"] - 1, length=2)
    return cb


def motion_arrows(ax, V, meta, step=25, color="0.1", key_kmh=None, timestep_min=15.0, mask=None,
                  scale=None):
    """ลูกศร motion field (pixel/timestep) — ลูกศร key แสดงเป็น km/h."""
    crs = get_crs(meta)
    X, Y = np.meshgrid(meta["x"], meta["y"])
    U = V[0] * meta["xpixelsize"]
    W = -V[1] * meta["ypixelsize"]          # yorigin = upper → กลับทิศให้ชี้ขึ้นเหนือ
    if mask is not None:
        U, W = np.where(mask, U, np.nan), np.where(mask, W, np.nan)
    s = (slice(step // 2, None, step), slice(step // 2, None, step))
    q = ax.quiver(X[s], Y[s], U[s], W[s], transform=crs, color=color, angles="xy",
                  scale_units="xy" if scale else None, scale=scale, width=0.003,
                  headwidth=3.5, zorder=7)
    spd = np.nanpercentile(np.hypot(U, W), 90) / 1000 * 60 / timestep_min
    k = key_kmh or max(10, int(round(spd / 10.0)) * 10)
    ax.quiverkey(q, 0.40, 0.05, k * 1000 * timestep_min / 60, f"{k} km h$^{{-1}}$", labelpos="N",
                 coordinates="axes", fontproperties={"size": 6}, color=color, labelcolor=color)
    return q


def plot_ppi(ax, radar, field, sweep, meta, cmap, norm, zoom=None):
    """แผนที่ PPI จากไฟล์ polar (Py-ART) บนระบบพิกัดเดียวกับข้อมูล pseudo-CAPPI."""
    crs = get_crs(meta)
    x, y, _ = radar.get_gate_x_y_z(sweep, edges=True)
    data = np.ma.masked_invalid(np.ma.filled(radar.fields[field]["data"].astype(float), np.nan)
                                [radar.get_slice(sweep)])
    ax.set_extent(zoom or extent_of(meta), crs=crs)
    return ax.pcolormesh(x, y, data, cmap=cmap, norm=norm, transform=crs, zorder=2,
                         rasterized=True)


# ---------------------------------------------------------------------------
# 6) กราฟและการบันทึก
# ---------------------------------------------------------------------------
def skill_axes(ax, xlabel="Lead time (min)", ylabel="", ylim=None, title=None):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.grid(True, linewidth=0.4, alpha=0.5)
    if title:
        ax.set_title(title, loc="left")
    return ax


def time_axis(ax, local_top=True, interval_h=2):
    """แกนเวลา UTC ด้านล่าง และเวลาท้องถิ่น (UTC+7) ด้านบน."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval_h))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel("Time (UTC)")
    if local_top:
        sec = ax.secondary_xaxis("top", functions=(lambda v: v + LOCAL_OFFSET_H / 24,
                                                   lambda v: v - LOCAL_OFFSET_H / 24))
        sec.xaxis.set_major_locator(mdates.HourLocator(interval=interval_h))
        sec.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        sec.set_xlabel("Local time (UTC+7)", fontsize=mpl.rcParams["axes.labelsize"] - 1)
    return ax


def save_figure(fig, name, folder=None, formats=("png", "pdf")):
    folder = folder or FIG_DIR
    os.makedirs(folder, exist_ok=True)
    paths = []
    for fmt in formats:
        p = os.path.join(folder, f"{name}.{fmt}")
        fig.savefig(p, dpi=300, bbox_inches="tight")
        paths.append(p)
    print("บันทึกรูปแล้ว:", ", ".join(paths))
    return paths


def tlabel(ts, local=True):
    """'09:30 UTC (16:30 LT)'"""
    s = ts.strftime("%H:%M UTC")
    if local:
        s += (ts + _dt.timedelta(hours=LOCAL_OFFSET_H)).strftime(" (%H:%M LT)")
    return s
