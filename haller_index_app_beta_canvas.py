
import streamlit as st
from PIL import Image
import math
import json
from pathlib import Path
from datetime import datetime
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Photographic Haller Index Beta", page_icon="🫁", layout="wide")

st.markdown("""
<style>
body {font-family: Arial, sans-serif;}
.block-container {max-width: 1400px; padding-top: 2rem;}
.info-box {
    background:#eff6ff; border-left:5px solid #2563eb; border-radius:12px;
    padding:1rem; margin:.8rem 0; color:#1e3a8a;
}
.warning-box {
    background:#fff7ed; border-left:5px solid #f97316; border-radius:12px;
    padding:1rem; margin:.8rem 0; color:#9a3412;
}
.metric-card {
    background:white; border:1px solid #dbe3ef; border-radius:18px;
    padding:1.4rem; text-align:center; margin:.5rem 0;
    box-shadow:0 8px 24px rgba(15,23,42,.06);
}
.metric-value {font-size:2.4rem; font-weight:800; color:#2563eb;}
.metric-label {
    font-size:.8rem; color:#64748b; text-transform:uppercase;
    letter-spacing:.08em; font-weight:700;
}
.result-normal,.result-borderline,.result-severe {
    border-radius:18px; padding:1.4rem; font-size:1.1rem;
    font-weight:700; text-align:center;
}
.result-normal {background:#ecfdf5; border:1.5px solid #86efac; color:#15803d;}
.result-borderline {background:#fffbeb; border:1.5px solid #facc15; color:#b45309;}
.result-severe {background:#fef2f2; border:1.5px solid #fca5a5; color:#b91c1c;}
</style>
""", unsafe_allow_html=True)

DATASET_DIR = Path("dataset")
IMAGES_DIR = DATASET_DIR / "images"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"

def ensure_dataset_dirs():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)

def resize_for_canvas(image, max_width=850):
    w, h = image.size
    if w <= max_width:
        return image.copy(), 1.0
    scale = max_width / w
    return image.resize((max_width, int(h * scale))), scale

def extract_circle_points(canvas_json):
    points = []
    if not canvas_json or "objects" not in canvas_json:
        return points
    for obj in canvas_json["objects"]:
        if obj.get("type") == "circle":
            left = float(obj.get("left", 0))
            top = float(obj.get("top", 0))
            radius = float(obj.get("radius", 0))
            points.append({"x": round(left + radius, 2), "y": round(top + radius, 2)})
    return points

def distance_pixels(p1, p2):
    return math.sqrt((p2["x"] - p1["x"]) ** 2 + (p2["y"] - p1["y"]) ** 2)

def calculate_measurement_cm(points, calibration_cm):
    if len(points) != 4:
        return None
    cal_px = distance_pixels(points[0], points[1])
    meas_px = distance_pixels(points[2], points[3])
    if cal_px == 0:
        return None
    return meas_px / (cal_px / calibration_cm)

def map_points_to_original(points, scale):
    if not points:
        return []
    if scale == 0:
        return points
    return [{"x": round(p["x"] / scale, 2), "y": round(p["y"] / scale, 2)} for p in points]

def interpretation(haller):
    if haller < 3.25:
        return "Normal range"
    if haller <= 3.5:
        return "Borderline range"
    return "Suggestive of pectus excavatum"

def render_result(haller):
    if haller < 3.25:
        cls = "result-normal"
        title = "✅ NORMAL RANGE"
        msg = "Screening result only. No diagnostic conclusion."
    elif haller <= 3.5:
        cls = "result-borderline"
        title = "⚠️ BORDERLINE RANGE"
        msg = "Screening result only. Clinical correlation required."
    else:
        cls = "result-severe"
        title = "🔴 SUGGESTIVE OF PECTUS EXCAVATUM"
        msg = "Screening result only. CT confirmation and specialist assessment required."
    st.markdown(
        f"<div class='{cls}'>{title} — Photographic Haller Index: {haller:.2f}<br>"
        f"<span style='font-size:.85rem;opacity:.8'>{msg}</span></div>",
        unsafe_allow_html=True,
    )

def render_canvas(title, uploaded_file, calibration_cm, key, anatomical_text, stroke_color):
    if uploaded_file is None:
        st.info(f"Upload the {title.lower()} image.")
        return None, [], [], None

    original = Image.open(uploaded_file)
    display, scale = resize_for_canvas(original, max_width=850)

    st.subheader(title)
    st.markdown(
        f"<div class='info-box'><b>Place exactly 4 circles:</b><br>"
        f"1. Calibration point A<br>"
        f"2. Calibration point B<br>"
        f"3. {anatomical_text} point 1<br>"
        f"4. {anatomical_text} point 2<br><br>"
        f"Use the circle tool. You can move circles after placing them.</div>",
        unsafe_allow_html=True,
    )

    canvas_result = st_canvas(
        fill_color="rgba(37, 99, 235, 0.35)",
        stroke_width=3,
        stroke_color=stroke_color,
        background_image=display,
        update_streamlit=True,
        height=display.height,
        width=display.width,
        drawing_mode="circle",
        point_display_radius=6,
        key=key,
    )

    points_display = extract_circle_points(canvas_result.json_data)
    points_original = map_points_to_original(points_display, scale)
    measurement_cm = calculate_measurement_cm(points_display, calibration_cm)

    st.caption(f"Detected points: {len(points_display)} / 4")
    if len(points_display) > 4:
        st.warning("More than 4 points detected. Delete extra circles on the canvas.")

    if measurement_cm is not None:
        st.markdown(
            f"<div class='metric-card'><div class='metric-value'>{measurement_cm:.1f} cm</div>"
            f"<div class='metric-label'>{title} measurement</div></div>",
            unsafe_allow_html=True,
        )

    return original, points_display, points_original, measurement_cm

st.title("🫁 Photographic Haller Index — Beta")
st.markdown("**Drawable Canvas version** · precise annotation + local patient saving")
st.markdown(
    "<div class='warning-box'>⚠️ Research prototype only. Non-diagnostic. Do not use for clinical decision-making.</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Protocol")
    st.write("Place exactly 4 circles on each image.")
    st.write("Frontal: calibration A/B + left/right thoracic border.")
    st.write("Lateral: calibration A/B + sternum/posterior point.")
    st.header("Storage")
    st.code("dataset/images/\ndataset/annotations/")

st.header("Patient metadata")
c1, c2, c3, c4 = st.columns(4)
with c1:
    patient_id = st.text_input("Anonymous Patient ID", value="PAT_0001")
with c2:
    age = st.number_input("Age", min_value=0, max_value=120, value=15, step=1)
with c3:
    sex = st.selectbox("Sex", ["Not specified", "Male", "Female", "Other"])
with c4:
    ct_haller = st.number_input("CT Haller Index if available", min_value=0.0, max_value=20.0, value=0.0, step=0.1)

clinical_note = st.text_area("Clinical note / comment", value="", height=80)

st.divider()
u1, u2 = st.columns(2)
with u1:
    face_file = st.file_uploader("Upload frontal photo", type=["jpg", "jpeg", "png"], key="face_upload")
    face_cal_cm = st.number_input("Frontal calibration length in cm", min_value=1.0, max_value=100.0, value=30.0, step=1.0)
with u2:
    profile_file = st.file_uploader("Upload strict lateral photo", type=["jpg", "jpeg", "png"], key="profile_upload")
    profile_cal_cm = st.number_input("Lateral calibration length in cm", min_value=1.0, max_value=100.0, value=30.0, step=1.0)

st.divider()
st.header("1. Frontal view — Transverse diameter")
face_img, face_pts_display, face_pts_original, face_cm = render_canvas(
    "Frontal view",
    face_file,
    face_cal_cm,
    "face_canvas",
    "Left/right thoracic border",
    "#2563eb",
)

st.divider()
st.header("2. Lateral view — Antero-posterior diameter")
profile_img, profile_pts_display, profile_pts_original, profile_cm = render_canvas(
    "Lateral view",
    profile_file,
    profile_cal_cm,
    "profile_canvas",
    "Anterior sternum/posterior vertebral",
    "#dc2626",
)

st.divider()
st.header("3. Result")
haller = None

if face_cm is not None and profile_cm is not None and len(face_pts_display) == 4 and len(profile_pts_display) == 4:
    if profile_cm > 0:
        haller = face_cm / profile_cm
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{face_cm:.1f} cm</div><div class='metric-label'>Transverse diameter</div></div>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{profile_cm:.1f} cm</div><div class='metric-label'>Antero-posterior diameter</div></div>", unsafe_allow_html=True)
        with r3:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{haller:.2f}</div><div class='metric-label'>Photographic Haller Index</div></div>", unsafe_allow_html=True)
        render_result(haller)
else:
    st.markdown("<div class='info-box'>Upload both photos and place exactly 4 circles on each image.</div>", unsafe_allow_html=True)

st.divider()
st.header("4. Save patient")

can_save = (
    patient_id.strip() != ""
    and face_img is not None
    and profile_img is not None
    and len(face_pts_display) == 4
    and len(profile_pts_display) == 4
    and haller is not None
)

if not can_save:
    st.markdown("<div class='info-box'>To save: patient ID + both images + exactly 4 points per image + calculated result.</div>", unsafe_allow_html=True)

if st.button("💾 Save Patient", disabled=not can_save):
    ensure_dataset_dirs()
    clean_id = patient_id.strip().replace(" ", "_")

    face_path = IMAGES_DIR / f"{clean_id}_face.jpg"
    profile_path = IMAGES_DIR / f"{clean_id}_profile.jpg"
    json_path = ANNOTATIONS_DIR / f"{clean_id}.json"

    face_img.convert("RGB").save(face_path, "JPEG", quality=95)
    profile_img.convert("RGB").save(profile_path, "JPEG", quality=95)

    annotation = {
        "patient_id": clean_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prototype_version": "beta_drawable_canvas_v1",
        "clinical_use": "research_prototype_non_diagnostic",
        "metadata": {
            "age": int(age),
            "sex": sex,
            "ct_haller_index": float(ct_haller) if ct_haller > 0 else None,
            "clinical_note": clinical_note,
        },
        "calibration": {
            "frontal_calibration_cm": float(face_cal_cm),
            "lateral_calibration_cm": float(profile_cal_cm),
        },
        "measurements": {
            "transverse_cm": round(float(face_cm), 3),
            "antero_posterior_cm": round(float(profile_cm), 3),
            "photographic_haller_index": round(float(haller), 3),
            "interpretation": interpretation(haller),
        },
        "points_display_coordinates": {
            "frontal": face_pts_display,
            "lateral": profile_pts_display,
        },
        "points_original_image_coordinates": {
            "frontal": face_pts_original,
            "lateral": profile_pts_original,
        },
        "image_files": {
            "frontal": str(face_path),
            "lateral": str(profile_path),
        },
        "privacy_note": "No name, date of birth, hospital ID or face should be stored in this dataset.",
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(annotation, f, indent=4, ensure_ascii=False)

    st.success(f"Patient saved: {clean_id}")
    st.code(f"Saved files:\n- {face_path}\n- {profile_path}\n- {json_path}")

if haller is not None:
    st.subheader("Annotation preview")
    st.json({
        "patient_id": patient_id,
        "transverse_cm": round(face_cm, 2),
        "antero_posterior_cm": round(profile_cm, 2),
        "photographic_haller_index": round(haller, 2),
        "face_points_display": face_pts_display,
        "profile_points_display": profile_pts_display,
        "face_points_original": face_pts_original,
        "profile_points_original": profile_pts_original,
    })
