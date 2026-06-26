import json
import math
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates


# =============================================================================
# CONFIG
# =============================================================================

st.set_page_config(
    page_title="Photographic Haller Index — Beta",
    page_icon="🫁",
    layout="wide",
)

DISPLAY_WIDTH = 850

DATASET_DIR = Path("dataset")
IMAGES_DIR = DATASET_DIR / "images"
ANNOTATIONS_DIR = DATASET_DIR / "annotations"


# =============================================================================
# BASIC STYLE
# =============================================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .small-note {
        color: #64748b;
        font-size: 0.9rem;
    }
    .warning-box {
        background: #fff7ed;
        border-left: 5px solid #f97316;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.8rem 0 1.2rem 0;
        color: #9a3412;
    }
    .info-box {
        background: #eff6ff;
        border-left: 5px solid #2563eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.8rem 0 1.2rem 0;
        color: #1e3a8a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# HELPERS
# =============================================================================

def ensure_dataset_dirs() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)


def clean_patient_id(raw_id: str) -> str:
    cleaned = raw_id.strip().replace(" ", "_")
    cleaned = "".join(c for c in cleaned if c.isalnum() or c in ["_", "-"])
    return cleaned or "PAT_UNKNOWN"


def resize_for_display(image: Image.Image, target_width: int = DISPLAY_WIDTH):
    """Return resized image and scale factor display/original."""
    original_width, original_height = image.size

    if original_width <= target_width:
        return image.copy(), 1.0

    scale = target_width / original_width
    target_height = int(original_height * scale)
    resized = image.resize((target_width, target_height))
    return resized, scale


def distance_px(point_a: dict, point_b: dict) -> float:
    return math.sqrt(
        (point_b["x"] - point_a["x"]) ** 2
        + (point_b["y"] - point_a["y"]) ** 2
    )


def calculate_cm(points: list, calibration_cm: float):
    """
    Points order:
    0 = calibration A
    1 = calibration B
    2 = measurement point 1
    3 = measurement point 2
    """
    if len(points) != 4:
        return None

    calibration_px = distance_px(points[0], points[1])
    measurement_px = distance_px(points[2], points[3])

    if calibration_px <= 0 or calibration_cm <= 0:
        return None

    px_per_cm = calibration_px / calibration_cm
    return measurement_px / px_per_cm


def map_points_to_original(points: list, scale: float) -> list:
    if scale == 0:
        return points

    return [
        {
            "x": round(point["x"] / scale, 2),
            "y": round(point["y"] / scale, 2),
        }
        for point in points
    ]


def interpretation(index: float) -> str:
    if index < 3.25:
        return "Normal range"
    if index <= 3.5:
        return "Borderline range"
    return "Suggestive of pectus excavatum"


def draw_annotations(
    image: Image.Image,
    points: list,
    labels: list,
    measurement_rgb: tuple,
) -> Image.Image:
    """Draw visible points and lines on display image."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    calibration_rgb = (245, 158, 11)  # orange
    white_rgb = (255, 255, 255)

    # Calibration line A-B
    if len(points) >= 2:
        draw.line(
            [
                (points[0]["x"], points[0]["y"]),
                (points[1]["x"], points[1]["y"]),
            ],
            fill=calibration_rgb,
            width=5,
        )

    # Measurement line
    if len(points) >= 4:
        draw.line(
            [
                (points[2]["x"], points[2]["y"]),
                (points[3]["x"], points[3]["y"]),
            ],
            fill=measurement_rgb,
            width=5,
        )

    # Points
    radius = 11
    for index, point in enumerate(points):
        x = point["x"]
        y = point["y"]
        color = calibration_rgb if index < 2 else measurement_rgb
        label = labels[index] if index < len(labels) else str(index + 1)

        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=color,
            outline=white_rgb,
            width=3,
        )

        # Label box
        label_x = x + 15
        label_y = y - 20
        draw.rounded_rectangle(
            [(label_x - 4, label_y - 2), (label_x + 28, label_y + 22)],
            radius=4,
            fill=color,
        )
        draw.text((label_x, label_y), label, fill=white_rgb)

    return annotated


def add_click_to_session(points_key: str, click: dict) -> None:
    if click is None:
        return

    if len(st.session_state[points_key]) >= 4:
        return

    point = {
        "x": int(click["x"]),
        "y": int(click["y"]),
    }

    # Avoid duplicate point from reruns
    if len(st.session_state[points_key]) == 0:
        st.session_state[points_key].append(point)
        st.rerun()

    if st.session_state[points_key][-1] != point:
        st.session_state[points_key].append(point)
        st.rerun()


def render_photo_section(
    title: str,
    uploaded_file,
    calibration_cm: float,
    points_key: str,
    labels: list,
    instructions: list,
    measurement_rgb: tuple,
):
    """
    Render one image section and return:
    original_image, display_points, original_points, measurement_cm
    """
    if uploaded_file is None:
        st.info(f"Upload the {title.lower()} image.")
        return None, [], [], None

    original_image = Image.open(uploaded_file).convert("RGB")
    display_image, scale = resize_for_display(original_image)
    current_points = st.session_state[points_key]

    annotated_image = draw_annotations(
        display_image,
        current_points,
        labels,
        measurement_rgb,
    )

    st.subheader(title)

    st.markdown(
        """
        <div class="info-box">
        <b>Click exactly 4 points in order.</b><br>
        Orange = calibration line. Colored line = measurement.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for number, instruction in enumerate(instructions, start=1):
        st.write(f"{number}. {instruction}")

    click = streamlit_image_coordinates(
        annotated_image,
        key=f"{points_key}_image_click",
        width=annotated_image.width,
    )

    add_click_to_session(points_key, click)

    controls_1, controls_2, controls_3 = st.columns([1, 1, 2])

    with controls_1:
        if st.button("Undo last point", key=f"undo_{points_key}"):
            if st.session_state[points_key]:
                st.session_state[points_key].pop()
                st.rerun()

    with controls_2:
        if st.button("Reset points", key=f"reset_{points_key}"):
            st.session_state[points_key] = []
            st.rerun()

    with controls_3:
        st.write(f"Selected points: **{len(st.session_state[points_key])}/4**")

    display_points = st.session_state[points_key]
    original_points = map_points_to_original(display_points, scale)
    measurement_cm = calculate_cm(display_points, calibration_cm)

    if measurement_cm is not None:
        st.metric(f"{title} measurement", f"{measurement_cm:.1f} cm")

    with st.expander("Show clicked coordinates"):
        st.json(display_points)

    return original_image, display_points, original_points, measurement_cm


# =============================================================================
# SESSION STATE
# =============================================================================

if "face_points" not in st.session_state:
    st.session_state.face_points = []

if "profile_points" not in st.session_state:
    st.session_state.profile_points = []


# =============================================================================
# HEADER
# =============================================================================

st.title("🫁 Photographic Haller Index — Beta")
st.markdown("**Visible-point version** · Streamlit Cloud compatible · JSON export")

st.markdown(
    """
    <div class="warning-box">
    <b>Research prototype only.</b><br>
    This tool is non-diagnostic and must not be used for clinical decision-making.
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("Protocol")
    st.write("Use thorax-only images without face or identifying elements.")
    st.write("Frontal view: calibration A/B + left/right thoracic border.")
    st.write("Lateral view: calibration A/B + AP measurement points.")
    st.write("Use the same calibration marker/ruler length for each image.")

    st.divider()

    if st.button("Reset all points"):
        st.session_state.face_points = []
        st.session_state.profile_points = []
        st.rerun()


# =============================================================================
# PATIENT METADATA
# =============================================================================

st.header("Patient metadata")

meta_1, meta_2, meta_3, meta_4 = st.columns(4)

with meta_1:
    patient_id = st.text_input("Patient ID", value="PAT_0001")

with meta_2:
    age = st.number_input("Age", min_value=0, max_value=120, value=15)

with meta_3:
    sex = st.selectbox("Sex", ["Not specified", "Male", "Female", "Other"])

with meta_4:
    ct_haller = st.number_input(
        "CT Haller Index if available",
        min_value=0.0,
        max_value=20.0,
        value=0.0,
        step=0.1,
    )

clinical_note = st.text_area(
    "Clinical note",
    value="",
    height=80,
    placeholder="Example: normal / mild pectus / moderate pectus / severe pectus",
)


# =============================================================================
# UPLOADS
# =============================================================================

st.divider()

upload_1, upload_2 = st.columns(2)

with upload_1:
    face_file = st.file_uploader(
        "Upload frontal photo",
        type=["jpg", "jpeg", "png"],
        key="face_file",
    )
    face_calibration_cm = st.number_input(
        "Frontal calibration length in cm",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
        key="face_calibration_cm",
    )

with upload_2:
    profile_file = st.file_uploader(
        "Upload lateral photo",
        type=["jpg", "jpeg", "png"],
        key="profile_file",
    )
    profile_calibration_cm = st.number_input(
        "Lateral calibration length in cm",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
        key="profile_calibration_cm",
    )


# =============================================================================
# FRONTAL SECTION
# =============================================================================

st.divider()

face_img, face_points, face_points_original, face_cm = render_photo_section(
    title="Frontal view",
    uploaded_file=face_file,
    calibration_cm=face_calibration_cm,
    points_key="face_points",
    labels=["A", "B", "L", "R"],
    instructions=[
        "Calibration point A",
        "Calibration point B",
        "Left thoracic border",
        "Right thoracic border",
    ],
    measurement_rgb=(37, 99, 235),  # blue
)


# =============================================================================
# LATERAL SECTION
# =============================================================================

st.divider()

profile_img, profile_points, profile_points_original, profile_cm = render_photo_section(
    title="Lateral view",
    uploaded_file=profile_file,
    calibration_cm=profile_calibration_cm,
    points_key="profile_points",
    labels=["A", "B", "1", "2"],
    instructions=[
        "Calibration point A",
        "Calibration point B",
        "AP measurement point 1",
        "AP measurement point 2",
    ],
    measurement_rgb=(220, 38, 38),  # red
)


# =============================================================================
# RESULT
# =============================================================================

st.divider()
st.header("Result")

photographic_index = None

if face_cm is not None and profile_cm is not None:
    photographic_index = face_cm / profile_cm

    result_1, result_2, result_3 = st.columns(3)

    with result_1:
        st.metric("Transverse diameter", f"{face_cm:.1f} cm")

    with result_2:
        st.metric("Antero-posterior diameter", f"{profile_cm:.1f} cm")

    with result_3:
        st.metric("Photographic Index", f"{photographic_index:.2f}")

    result_text = interpretation(photographic_index)

    if photographic_index < 3.25:
        st.success(f"{result_text} — Photographic Index: {photographic_index:.2f}")
    elif photographic_index <= 3.5:
        st.warning(f"{result_text} — Photographic Index: {photographic_index:.2f}")
    else:
        st.error(f"{result_text} — Photographic Index: {photographic_index:.2f}")
else:
    st.info("Upload both images and click exactly 4 points on each image.")


# =============================================================================
# SAVE
# =============================================================================

st.divider()
st.header("Save patient")

can_save = (
    patient_id.strip() != ""
    and face_img is not None
    and profile_img is not None
    and len(face_points) == 4
    and len(profile_points) == 4
    and photographic_index is not None
)

if not can_save:
    st.info("To save: patient ID + both images + exactly 4 points on each image + calculated index.")

if st.button("💾 Save Patient", disabled=not can_save):
    ensure_dataset_dirs()

    clean_id = clean_patient_id(patient_id)

    face_path = IMAGES_DIR / f"{clean_id}_face.jpg"
    profile_path = IMAGES_DIR / f"{clean_id}_profile.jpg"
    annotation_path = ANNOTATIONS_DIR / f"{clean_id}.json"

    face_img.save(face_path, "JPEG", quality=95)
    profile_img.save(profile_path, "JPEG", quality=95)

    annotation = {
        "patient_id": clean_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prototype_version": "cloud_visible_points_v2",
        "clinical_use": "research_prototype_non_diagnostic",
        "metadata": {
            "age": int(age),
            "sex": sex,
            "ct_haller_index": float(ct_haller) if ct_haller > 0 else None,
            "clinical_note": clinical_note,
        },
        "calibration": {
            "frontal_calibration_cm": float(face_calibration_cm),
            "lateral_calibration_cm": float(profile_calibration_cm),
        },
        "measurements": {
            "transverse_cm": round(float(face_cm), 3),
            "antero_posterior_cm": round(float(profile_cm), 3),
            "photographic_index": round(float(photographic_index), 3),
            "interpretation": interpretation(photographic_index),
        },
        "points_display_coordinates": {
            "frontal": face_points,
            "lateral": profile_points,
        },
        "points_original_image_coordinates": {
            "frontal": face_points_original,
            "lateral": profile_points_original,
        },
        "image_files": {
            "frontal": str(face_path),
            "lateral": str(profile_path),
        },
        "privacy_note": "No name, date of birth, hospital ID, face or identifying information should be stored.",
    }

    with open(annotation_path, "w", encoding="utf-8") as file:
        json.dump(annotation, file, indent=4, ensure_ascii=False)

    st.success(f"Patient saved: {clean_id}")
    st.code(
        f"Saved files:\n"
        f"- {face_path}\n"
        f"- {profile_path}\n"
        f"- {annotation_path}"
    )

if photographic_index is not None:
    st.subheader("Annotation preview")
    st.json(
        {
            "patient_id": patient_id,
            "transverse_cm": round(face_cm, 2),
            "antero_posterior_cm": round(profile_cm, 2),
            "photographic_index": round(photographic_index, 2),
            "face_points": face_points,
            "profile_points": profile_points,
        }
    )
    if w <= width:
    return image.copy(), 1.0
    scale = width / w
    return image.resize((width, int(h * scale))), scale


def distance(p1, p2):
    return math.sqrt((p2["x"] - p1["x"]) ** 2 + (p2["y"] - p1["y"]) ** 2)


def measure_cm(points, calibration_cm):
    if len(points) != 4:
        return None

    cal_px = distance(points[0], points[1])
    meas_px = distance(points[2], points[3])

    if cal_px <= 0 or calibration_cm <= 0:
        return None

    return meas_px / (cal_px / calibration_cm)


def to_original(points, scale):
    if scale == 0:
        return points
    return [{"x": round(p["x"] / scale, 2), "y": round(p["y"] / scale, 2)} for p in points]


def interpretation(index):
    if index < 3.25:
        return "Normal range"
    if index <= 3.5:
        return "Borderline range"
    return "Suggestive of pectus excavatum"


def add_point(key, click):
    if click is None:
        return

    if len(st.session_state[key]) >= 4:
        return

    point = {"x": int(click["x"]), "y": int(click["y"])}

    # Avoid duplicate click generated by rerun
    if len(st.session_state[key]) == 0 or st.session_state[key][-1] != point:
        st.session_state[key].append(point)
        st.rerun()


def draw_annotations(image: Image.Image, points, labels, measurement_color):
    img = image.copy()
    draw = ImageDraw.Draw(img)

    # Colors
    calibration_color = (245, 158, 11)  # orange
    white = (255, 255, 255)

    # Draw calibration line A-B
    if len(points) >= 2:
        p1, p2 = points[0], points[1]
        draw.line(
            [(p1["x"], p1["y"]), (p2["x"], p2["y"])],
            fill=calibration_color,
            width=5,
        )

    # Draw measurement line 1-2
    if len(points) >= 4:
        p1, p2 = points[2], points[3]
        draw.line(
            [(p1["x"], p1["y"]), (p2["x"], p2["y"])],
            fill=measurement_color,
            width=5,
        )

    # Draw points
    radius = 11
    for i, p in enumerate(points):
        x, y = p["x"], p["y"]
        color = calibration_color if i < 2 else measurement_color
        label = labels[i] if i < len(labels) else str(i + 1)

        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=color,
            outline=white,
            width=3,
        )

        # Label background
        text_x, text_y = x + 14, y - 18
        draw.rectangle(
            [(text_x - 3, text_y - 2), (text_x + 24, text_y + 20)],
            fill=color,
        )
        draw.text((text_x, text_y), label, fill=white)

    return img


def render_click_section(
    title,
    uploaded_file,
    points_key,
    calibration_cm,
    instructions,
    labels,
    measurement_color,
):
    if uploaded_file is None:
        st.info(f"Upload the {title.lower()} image.")
        return None, [], [], None

    original_image = Image.open(uploaded_file).convert("RGB")
    display_image, scale = resize_image(original_image)

    annotated_image = draw_annotations(
        display_image,
        st.session_state[points_key],
        labels,
        measurement_color,
    )

    st.subheader(title)

    st.markdown("**Click exactly 4 points in this order:**")
    for i, instruction in enumerate(instructions, start=1):
        st.write(f"{i}. {instruction}")

    click = streamlit_image_coordinates(
        annotated_image,
        key=f"{points_key}_click_widget",
        width=annotated_image.width,
    )

    add_point(points_key, click)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Undo last point", key=f"undo_{points_key}"):
            if st.session_state[points_key]:
                st.session_state[points_key].pop()
                st.rerun()

    with col2:
        if st.button("Reset points", key=f"reset_{points_key}"):
            st.session_state[points_key] = []
            st.rerun()

    with col3:
        st.write(f"Selected: **{len(st.session_state[points_key])}/4**")

    points = st.session_state[points_key]
    measurement = measure_cm(points, calibration_cm)
    points_original = to_original(points, scale)

    if measurement is not None:
        st.metric(f"{title} measurement", f"{measurement:.1f} cm")

    with st.expander("Show clicked coordinates"):
        st.json(points)

    return original_image, points, points_original, measurement


# ──────────────────────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────────────────────
if "face_points" not in st.session_state:
    st.session_state.face_points = []

if "profile_points" not in st.session_state:
    st.session_state.profile_points = []

# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.title("🫁 Photographic Haller Index — Beta")
st.markdown("**Cloud-compatible version** · visible points · 4 clicks per image · JSON export")
st.warning("Research prototype only. Non-diagnostic. Do not use for clinical decision-making.")

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Protocol")
    st.write("Use thorax-only photos without face or identifying markers.")
    st.write("Face: calibration A/B + left/right thoracic border.")
    st.write("Profile: calibration A/B + AP measurement points.")
    st.write("The orange line is calibration. The blue/red line is the measurement.")

    if st.button("Reset all points"):
        st.session_state.face_points = []
        st.session_state.profile_points = []
        st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Metadata
# ──────────────────────────────────────────────────────────────────────────────
st.header("Patient metadata")

m1, m2, m3, m4 = st.columns(4)

with m1:
    patient_id = st.text_input("Patient ID", value="PAT_0001")

with m2:
    age = st.number_input("Age", min_value=0, max_value=120, value=15)

with m3:
    sex = st.selectbox("Sex", ["Not specified", "Male", "Female", "Other"])

with m4:
    ct_haller = st.number_input(
        "CT Haller Index if available",
        min_value=0.0,
        max_value=20.0,
        value=0.0,
        step=0.1,
    )

clinical_note = st.text_area(
    "Clinical note",
    value="",
    height=80,
    placeholder="Example: normal / mild pectus / moderate pectus / severe pectus",
)

# ──────────────────────────────────────────────────────────────────────────────
# Uploads
# ──────────────────────────────────────────────────────────────────────────────
st.divider()

u1, u2 = st.columns(2)

with u1:
    face_file = st.file_uploader(
        "Upload frontal photo",
        type=["jpg", "jpeg", "png"],
        key="face_file",
    )
    face_cal_cm = st.number_input(
        "Frontal calibration length in cm",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
        key="face_cal",
    )

with u2:
    profile_file = st.file_uploader(
        "Upload lateral photo",
        type=["jpg", "jpeg", "png"],
        key="profile_file",
    )
    profile_cal_cm = st.number_input(
        "Lateral calibration length in cm",
        min_value=1.0,
        max_value=100.0,
        value=30.0,
        step=1.0,
        key="profile_cal",
    )

# ──────────────────────────────────────────────────────────────────────────────
# Frontal view
# ──────────────────────────────────────────────────────────────────────────────
st.divider()

face_img, face_points, face_points_original, face_cm = render_click_section(
    title="Frontal view",
    uploaded_file=face_file,
    points_key="face_points",
    calibration_cm=face_cal_cm,
    instructions=[
        "Calibration point A",
        "Calibration point B",
        "Left thoracic border",
        "Right thoracic border",
    ],
    labels=["A", "B", "L", "R"],
    measurement_color=(37, 99, 235),  # blue
)

# ──────────────────────────────────────────────────────────────────────────────
# Lateral view
# ──────────────────────────────────────────────────────────────────────────────
st.divider()

profile_img, profile_points, profile_points_original, profile_cm = render_click_section(
    title="Lateral view",
    uploaded_file=profile_file,
    points_key="profile_points",
    calibration_cm=profile_cal_cm,
    instructions=[
        "Calibration point A",
        "Calibration point B",
        "AP point 1",
        "AP point 2",
    ],
    labels=["A", "B", "1", "2"],
    measurement_color=(220, 38, 38),  # red
)

# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────
st.divider()
st.header("Result")

photographic_index = None

if face_cm is not None and profile_cm is not None:
    photographic_index = face_cm / profile_cm

    r1, r2, r3 = st.columns(3)

    with r1:
        st.metric("Transverse diameter", f"{face_cm:.1f} cm")

    with r2:
        st.metric("Antero-posterior diameter", f"{profile_cm:.1f} cm")

    with r3:
        st.metric("Photographic Index", f"{photographic_index:.2f}")

    interp = interpretation(photographic_index)

    if photographic_index < 3.25:
        st.success(f"{interp} — Photographic Index: {photographic_index:.2f}")
    elif photographic_index <= 3.5:
        st.warning(f"{interp} — Photographic Index: {photographic_index:.2f}")
    else:
        st.error(f"{interp} — Photographic Index: {photographic_index:.2f}")

else:
    st.info("Upload both images and click exactly 4 points on each image.")

# ──────────────────────────────────────────────────────────────────────────────
# Save
# ──────────────────────────────────────────────────────────────────────────────
st.divider()
st.header("Save patient")

can_save = (
    patient_id.strip() != ""
    and face_img is not None
    and profile_img is not None
    and len(face_points) == 4
    and len(profile_points) == 4
    and photographic_index is not None
)

if not can_save:
    st.info("To save: patient ID + both images + exactly 4 points on each image + calculated index.")

if st.button("💾 Save Patient", disabled=not can_save):
    ensure_dirs()

    clean_id = patient_id.strip().replace(" ", "_")

    face_path = IMAGES_DIR / f"{clean_id}_face.jpg"
    profile_path = IMAGES_DIR / f"{clean_id}_profile.jpg"
    json_path = ANNOTATIONS_DIR / f"{clean_id}.json"

    face_img.save(face_path, "JPEG", quality=95)
    profile_img.save(profile_path, "JPEG", quality=95)

    annotation = {
        "patient_id": clean_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prototype_version": "cloud_click_visible_points_v1",
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
            "photographic_index": round(float(photographic_index), 3),
            "interpretation": interpretation(photographic_index),
        },
        "points_display_coordinates": {
            "frontal": face_points,
            "lateral": profile_points,
        },
        "points_original_image_coordinates": {
            "frontal": face_points_original,
            "lateral": profile_points_original,
        },
        "image_files": {
            "frontal": str(face_path),
            "lateral": str(profile_path),
        },
        "privacy_note": "No name, date of birth, hospital ID, face or identifying information should be stored.",
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(annotation, f, indent=4, ensure_ascii=False)

    st.success(f"Patient saved: {clean_id}")
    st.code(f"Saved files:\n- {face_path}\n- {profile_path}\n- {json_path}")

if photographic_index is not None:
    st.subheader("Annotation preview")
    st.json({
        "patient_id": patient_id,
        "transverse_cm": round(face_cm, 2),
        "antero_posterior_cm": round(profile_cm, 2),
        "photographic_index": round(photographic_index, 2),
        "face_points": face_points,
        "profile_points": profile_points,
    })
    cal_px = dist(points[0], points[1])
    meas_px = dist(points[2], points[3])
    if cal_px == 0:
        return None
    return meas_px / (cal_px / calibration_cm)

def to_original(points, scale):
    if scale == 0:
        return points
    return [{"x": round(p["x"] / scale, 2), "y": round(p["y"] / scale, 2)} for p in points]

def interpretation(index):
    if index < 3.25:
        return "Normal range"
    if index <= 3.5:
        return "Borderline range"
    return "Suggestive of pectus excavatum"

def add_point(key, click):
    if click is None or len(st.session_state[key]) >= 4:
        return
    point = {"x": int(click["x"]), "y": int(click["y"])}
    if len(st.session_state[key]) == 0 or st.session_state[key][-1] != point:
        st.session_state[key].append(point)
        st.rerun()

def image_click_block(title, uploaded_file, points_key, calibration_cm, instructions):
    if uploaded_file is None:
        st.info(f"Upload {title.lower()} image.")
        return None, [], [], None

    image = Image.open(uploaded_file).convert("RGB")
    display_image, scale = resize_image(image)

    st.subheader(title)
    st.markdown("Click exactly 4 points in this order:")
    for i, text in enumerate(instructions, start=1):
        st.write(f"{i}. {text}")

    click = streamlit_image_coordinates(display_image, key=f"{points_key}_widget", width=display_image.width)
    add_point(points_key, click)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Undo last point", key=f"undo_{points_key}"):
            if st.session_state[points_key]:
                st.session_state[points_key].pop()
                st.rerun()
    with col2:
        if st.button("Reset points", key=f"reset_{points_key}"):
            st.session_state[points_key] = []
            st.rerun()

    points = st.session_state[points_key]
    st.write(f"Selected points: {len(points)} / 4")
    st.json(points)

    measurement = measure_cm(points, calibration_cm)
    points_original = to_original(points, scale)

    if measurement is not None:
        st.metric(f"{title} measurement", f"{measurement:.1f} cm")

    return image, points, points_original, measurement

if "face_points" not in st.session_state:
    st.session_state.face_points = []
if "profile_points" not in st.session_state:
    st.session_state.profile_points = []

with st.sidebar:
    st.header("Protocol")
    st.write("Face: calibration A/B + left/right thoracic border.")
    st.write("Profile: calibration A/B + AP measurement points.")
    if st.button("Reset all"):
        st.session_state.face_points = []
        st.session_state.profile_points = []
        st.rerun()

st.header("Patient metadata")
c1, c2, c3, c4 = st.columns(4)
with c1:
    patient_id = st.text_input("Patient ID", value="PAT_0001")
with c2:
    age = st.number_input("Age", min_value=0, max_value=120, value=15)
with c3:
    sex = st.selectbox("Sex", ["Not specified", "Male", "Female", "Other"])
with c4:
    ct_haller = st.number_input("CT Haller Index if available", min_value=0.0, max_value=20.0, value=0.0, step=0.1)

clinical_note = st.text_area("Clinical note", value="", height=80)

st.divider()
u1, u2 = st.columns(2)
with u1:
    face_file = st.file_uploader("Upload frontal photo", type=["jpg", "jpeg", "png"], key="face_file")
    face_cal_cm = st.number_input("Frontal calibration length in cm", min_value=1.0, max_value=100.0, value=30.0, step=1.0)
with u2:
    profile_file = st.file_uploader("Upload lateral photo", type=["jpg", "jpeg", "png"], key="profile_file")
    profile_cal_cm = st.number_input("Lateral calibration length in cm", min_value=1.0, max_value=100.0, value=30.0, step=1.0)

st.divider()
face_img, face_points, face_points_original, face_cm = image_click_block(
    "Frontal view", face_file, "face_points", face_cal_cm,
    ["Calibration point A", "Calibration point B", "Left thoracic border", "Right thoracic border"]
)

st.divider()
profile_img, profile_points, profile_points_original, profile_cm = image_click_block(
    "Lateral view", profile_file, "profile_points", profile_cal_cm,
    ["Calibration point A", "Calibration point B", "AP point 1", "AP point 2"]
)

st.divider()
st.header("Result")
haller = None
if face_cm is not None and profile_cm is not None:
    haller = face_cm / profile_cm
    r1, r2, r3 = st.columns(3)
    r1.metric("Transverse diameter", f"{face_cm:.1f} cm")
    r2.metric("Antero-posterior diameter", f"{profile_cm:.1f} cm")
    r3.metric("Photographic Index", f"{haller:.2f}")

    interp = interpretation(haller)
    if haller < 3.25:
        st.success(f"{interp} — Photographic Index: {haller:.2f}")
    elif haller <= 3.5:
        st.warning(f"{interp} — Photographic Index: {haller:.2f}")
    else:
        st.error(f"{interp} — Photographic Index: {haller:.2f}")
else:
    st.info("Upload both images and click 4 points on each image.")

st.divider()
st.header("Save patient")

can_save = (
    patient_id.strip() != ""
    and face_img is not None
    and profile_img is not None
    and len(face_points) == 4
    and len(profile_points) == 4
    and haller is not None
)

if st.button("💾 Save Patient", disabled=not can_save):
    ensure_dirs()
    clean_id = patient_id.strip().replace(" ", "_")
    face_path = IMAGES_DIR / f"{clean_id}_face.jpg"
    profile_path = IMAGES_DIR / f"{clean_id}_profile.jpg"
    json_path = ANNOTATIONS_DIR / f"{clean_id}.json"

    face_img.save(face_path, "JPEG", quality=95)
    profile_img.save(profile_path, "JPEG", quality=95)

    annotation = {
        "patient_id": clean_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "prototype_version": "cloud_click_v1",
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
            "photographic_index": round(float(haller), 3),
            "interpretation": interpretation(haller),
        },
        "points_display_coordinates": {
            "frontal": face_points,
            "lateral": profile_points,
        },
        "points_original_image_coordinates": {
            "frontal": face_points_original,
            "lateral": profile_points_original,
        },
        "image_files": {
            "frontal": str(face_path),
            "lateral": str(profile_path),
        },
        "privacy_note": "No name, date of birth, hospital ID or face should be stored.",
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
        "photographic_index": round(haller, 2),
        "face_points": face_points,
        "profile_points": profile_points,
    })
