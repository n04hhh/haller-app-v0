import streamlit as st
import numpy as np
from PIL import Image
import math

# ─── Page configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Haller Index",
    page_icon="🫁",
    layout="wide",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #f6f8fb;
    --surface: #ffffff;
    --surface-soft: #f9fbfd;
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --primary-soft: #eff6ff;
    --success: #15803d;
    --success-bg: #ecfdf5;
    --warning: #b45309;
    --warning-bg: #fffbeb;
    --danger: #b91c1c;
    --danger-bg: #fef2f2;
    --text: #0f172a;
    --muted: #64748b;
    --border: #dbe3ef;
    --shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1300px;
}

[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--border);
    box-shadow: 4px 0 20px rgba(15,23,42,0.03);
}

h1 {
    color: var(--text) !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em;
    font-size: 2.6rem !important;
}

h2 {
    color: var(--text) !important;
    font-weight: 750 !important;
    letter-spacing: -0.03em;
    margin-top: 1.5rem !important;
}

h3, h4 {
    color: #1e293b !important;
    font-weight: 700 !important;
}

p, li, label, span, div {
    font-family: 'Inter', sans-serif !important;
}

hr {
    border: none !important;
    height: 1px !important;
    background: var(--border) !important;
    margin: 2rem 0 !important;
}

.stButton > button {
    background: var(--primary);
    color: white;
    font-weight: 700;
    border: none;
    border-radius: 10px;
    padding: 0.75rem 1.4rem;
    width: 100%;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
    transition: 0.2s ease;
}

.stButton > button:hover {
    background: var(--primary-dark);
    transform: translateY(-1px);
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.24);
}

.stFileUploader {
    background: var(--surface) !important;
    border: 1.5px dashed #b8c4d6 !important;
    border-radius: 14px !important;
    padding: 1rem !important;
}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 0.55rem 0.75rem !important;
}

[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.6rem 1.2rem;
    text-align: center;
    margin: 0.5rem 0;
    box-shadow: var(--shadow);
}

.metric-value {
    font-size: 2.7rem;
    line-height: 1;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -0.04em;
}

.metric-label {
    font-size: 0.78rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-top: 0.65rem;
    font-weight: 700;
}

.result-normal,
.result-borderline,
.result-severe {
    border-radius: 18px;
    padding: 1.6rem;
    font-size: 1.15rem;
    font-weight: 750;
    text-align: center;
    box-shadow: var(--shadow);
}

.result-normal {
    background: var(--success-bg);
    border: 1.5px solid #86efac;
    color: var(--success);
}

.result-borderline {
    background: var(--warning-bg);
    border: 1.5px solid #facc15;
    color: var(--warning);
}

.result-severe {
    background: var(--danger-bg);
    border: 1.5px solid #fca5a5;
    color: var(--danger);
}

.step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--primary);
    color: white;
    font-weight: 800;
    border-radius: 999px;
    width: 32px;
    height: 32px;
    margin-right: 10px;
    font-size: 0.95rem;
}

.info-box {
    background: var(--primary-soft);
    border: 1px solid #bfdbfe;
    border-left: 5px solid var(--primary);
    border-radius: 12px;
    padding: 0.95rem 1rem;
    margin: 0.8rem 0;
    font-size: 0.92rem;
    color: #1e3a8a;
    line-height: 1.5;
}

.stAlert {
    border-radius: 14px !important;
}

[data-testid="stSidebar"] table {
    font-size: 0.85rem;
}

[data-testid="stSidebar"] code {
    background: #f1f5f9 !important;
    color: #0f172a !important;
    border-radius: 8px;
    padding: 0.75rem;
}

img {
    border-radius: 14px;
}

[data-testid="stImageCaption"] {
    color: var(--muted) !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("# 🫁 Haller Index")
st.markdown("**Photographic screening tool for Pectus Excavatum** · Phase 1 · Clinical prototype")
st.markdown("---")


# ─── Sidebar: instructions ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📋 Instructions")
    st.markdown("""
    <div class='info-box'>
    <b>Photo protocol</b><br>
    Make sure a ruler or calibration marker is visible in both photos.
    The patient should stand in a standard anatomical position with arms slightly away from the body.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    **Frontal view**
    - Capture the maximum transverse width of the chest
    - Place the ruler horizontally against the skin
    - Keep the camera as perpendicular as possible

    **Strict lateral view**
    - Patient must be in true profile position
    - The ruler must remain clearly visible
    - Avoid rotation or perspective distortion
    """)

    st.markdown("---")
    st.markdown("## 📐 Haller Index")
    st.markdown("""
    ```
    HI = Transverse diameter
         ────────────────────
         Antero-posterior diameter
    ```
    | Value | Interpretation |
    |-------|----------------|
    | < 3.25 | Normal range |
    | 3.25 – 3.5 | Borderline |
    | > 3.5 | Suggestive of Pectus Excavatum |
    """)

    st.markdown("---")
    st.markdown(
        "<div style='color:#64748b;font-size:0.75rem;'>"
        "⚠️ Screening prototype only. This tool does not replace CT imaging or specialist evaluation."
        "</div>",
        unsafe_allow_html=True
    )


# ─── Helper functions ─────────────────────────────────────────────────────────
def distance_pixels(p1, p2):
    """Calculate Euclidean distance between two points in pixels."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def draw_points_and_line(img_array, points, color=(37, 99, 235), radius=10):
    """Draw measurement points and line on the image."""
    import cv2

    img = img_array.copy()

    if len(points) >= 2:
        cv2.line(img, tuple(points[0]), tuple(points[1]), color, 3)

    for i, p in enumerate(points):
        cv2.circle(img, tuple(p), radius, color, -1)
        cv2.circle(img, tuple(p), radius + 3, (255, 255, 255), 2)
        cv2.putText(
            img,
            str(i + 1),
            (p[0] + 12, p[1] + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    return img


def pil_to_array(pil_img):
    """Convert PIL image to RGB numpy array."""
    return np.array(pil_img.convert("RGB"))


# ─── Session state initialization ─────────────────────────────────────────────
for key in ["face_cal_pts", "face_pts", "profile_cal_pts", "profile_pts"]:
    if key not in st.session_state:
        st.session_state[key] = []


# ─── Section 1: Frontal view ──────────────────────────────────────────────────
st.markdown(
    "## <span class='step-badge'>1</span> Frontal view — Transverse diameter",
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1])

with col1:
    face_file = st.file_uploader(
        "📸 Upload frontal photo",
        type=["jpg", "jpeg", "png"],
        key="face_upload"
    )

with col2:
    if face_file:
        face_img = Image.open(face_file)
        face_arr = pil_to_array(face_img)
        W_face, H_face = face_img.size

        st.markdown("**Ruler width in the frontal photo**")
        st.markdown(
            "<div class='info-box'>"
            "Enter the pixel coordinates manually for now. In the next version, this will be replaced by direct clicks on the image."
            "</div>",
            unsafe_allow_html=True
        )

        # Frontal calibration
        st.markdown("#### 📏 Calibration — Ruler")
        cal_face_x1 = st.number_input("Point A — X (px)", 0, W_face, W_face // 4, key="fcx1")
        cal_face_y1 = st.number_input("Point A — Y (px)", 0, H_face, H_face // 2, key="fcy1")
        cal_face_x2 = st.number_input("Point B — X (px)", 0, W_face, W_face // 2, key="fcx2")
        cal_face_y2 = st.number_input("Point B — Y (px)", 0, H_face, H_face // 2, key="fcy2")
        cal_face_cm = st.number_input("Real ruler length (cm)", 1.0, 100.0, 30.0, key="fcm")

        st.markdown("#### 📐 Transverse diameter")
        trans_x1 = st.number_input("Left chest border — X (px)", 0, W_face, W_face // 4, key="tx1")
        trans_y1 = st.number_input("Left chest border — Y (px)", 0, H_face, H_face // 2, key="ty1")
        trans_x2 = st.number_input("Right chest border — X (px)", 0, W_face, 3 * W_face // 4, key="tx2")
        trans_y2 = st.number_input("Right chest border — Y (px)", 0, H_face, H_face // 2, key="ty2")

        # Calibration calculation
        cal_face_px = distance_pixels([cal_face_x1, cal_face_y1], [cal_face_x2, cal_face_y2])
        px_per_cm_face = cal_face_px / cal_face_cm if cal_face_cm > 0 else 1

        trans_px = distance_pixels([trans_x1, trans_y1], [trans_x2, trans_y2])
        trans_cm = trans_px / px_per_cm_face

        # Display annotated image
        img_annotated = face_arr.copy()
        img_annotated = draw_points_and_line(
            img_annotated,
            [[cal_face_x1, cal_face_y1], [cal_face_x2, cal_face_y2]],
            color=(245, 158, 11)
        )
        img_annotated = draw_points_and_line(
            img_annotated,
            [[trans_x1, trans_y1], [trans_x2, trans_y2]],
            color=(37, 99, 235)
        )

        st.image(
            img_annotated,
            caption="🟠 Calibration ruler | 🔵 Transverse diameter",
            use_container_width=True
        )

        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{trans_cm:.1f} cm</div>
            <div class='metric-label'>Transverse diameter</div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state["trans_cm"] = trans_cm
    else:
        st.info("⬆️ Upload a frontal photo to start.")


# ─── Section 2: Lateral view ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "## <span class='step-badge'>2</span> Lateral view — Antero-posterior diameter",
    unsafe_allow_html=True
)

col3, col4 = st.columns([1, 1])

with col3:
    profile_file = st.file_uploader(
        "📸 Upload strict lateral photo",
        type=["jpg", "jpeg", "png"],
        key="profile_upload"
    )

with col4:
    if profile_file:
        profile_img = Image.open(profile_file)
        profile_arr = pil_to_array(profile_img)
        W_profile, H_profile = profile_img.size

        st.markdown("#### 📏 Calibration — Ruler")
        cal_p_x1 = st.number_input("Point A — X (px)", 0, W_profile, W_profile // 4, key="pcx1")
        cal_p_y1 = st.number_input("Point A — Y (px)", 0, H_profile, H_profile // 2, key="pcy1")
        cal_p_x2 = st.number_input("Point B — X (px)", 0, W_profile, W_profile // 2, key="pcx2")
        cal_p_y2 = st.number_input("Point B — Y (px)", 0, H_profile, H_profile // 2, key="pcy2")
        cal_p_cm = st.number_input("Real ruler length (cm)", 1.0, 100.0, 30.0, key="pcm")

        st.markdown("#### 📐 Antero-posterior diameter")
        ap_x1 = st.number_input("Anterior sternum — X (px)", 0, W_profile, W_profile // 3, key="ax1")
        ap_y1 = st.number_input("Anterior sternum — Y (px)", 0, H_profile, H_profile // 2, key="ay1")
        ap_x2 = st.number_input("Posterior vertebral point — X (px)", 0, W_profile, 2 * W_profile // 3, key="ax2")
        ap_y2 = st.number_input("Posterior vertebral point — Y (px)", 0, H_profile, H_profile // 2, key="ay2")

        cal_p_px = distance_pixels([cal_p_x1, cal_p_y1], [cal_p_x2, cal_p_y2])
        px_per_cm_profile = cal_p_px / cal_p_cm if cal_p_cm > 0 else 1

        ap_px = distance_pixels([ap_x1, ap_y1], [ap_x2, ap_y2])
        ap_cm = ap_px / px_per_cm_profile

        img_p_annotated = profile_arr.copy()
        img_p_annotated = draw_points_and_line(
            img_p_annotated,
            [[cal_p_x1, cal_p_y1], [cal_p_x2, cal_p_y2]],
            color=(245, 158, 11)
        )
        img_p_annotated = draw_points_and_line(
            img_p_annotated,
            [[ap_x1, ap_y1], [ap_x2, ap_y2]],
            color=(220, 38, 38)
        )

        st.image(
            img_p_annotated,
            caption="🟠 Calibration ruler | 🔴 Antero-posterior diameter",
            use_container_width=True
        )

        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{ap_cm:.1f} cm</div>
            <div class='metric-label'>Antero-posterior diameter</div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state["ap_cm"] = ap_cm
    else:
        st.info("⬆️ Upload a strict lateral photo to continue.")


# ─── Section 3: Result ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "## <span class='step-badge'>3</span> Result — Photographic Haller Index",
    unsafe_allow_html=True
)

if "trans_cm" in st.session_state and "ap_cm" in st.session_state:
    trans = st.session_state["trans_cm"]
    ap = st.session_state["ap_cm"]

    if ap > 0:
        haller = trans / ap

        col5, col6, col7 = st.columns(3)

        with col5:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{trans:.1f} cm</div>
                <div class='metric-label'>Transverse diameter</div>
            </div>
            """, unsafe_allow_html=True)

        with col6:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{ap:.1f} cm</div>
                <div class='metric-label'>Antero-posterior diameter</div>
            </div>
            """, unsafe_allow_html=True)

        with col7:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value' style='font-size:3rem'>{haller:.2f}</div>
                <div class='metric-label'>Photographic Haller Index</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if haller < 3.25:
            st.markdown(f"""
            <div class='result-normal'>
                ✅ NORMAL RANGE — Photographic Haller Index: {haller:.2f}<br>
                <span style='font-size:0.85rem;opacity:0.8'>
                No photographic sign suggesting severe pectus excavatum based on this threshold.
                </span>
            </div>
            """, unsafe_allow_html=True)

        elif haller <= 3.5:
            st.markdown(f"""
            <div class='result-borderline'>
                ⚠️ BORDERLINE RANGE — Photographic Haller Index: {haller:.2f}<br>
                <span style='font-size:0.85rem;opacity:0.8'>
                Borderline range. Clinical correlation and CT confirmation are recommended if relevant.
                </span>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div class='result-severe'>
                🔴 SUGGESTIVE OF PECTUS EXCAVATUM — Photographic Haller Index: {haller:.2f}<br>
                <span style='font-size:0.85rem;opacity:0.8'>
                Index above threshold. Specialist evaluation and CT confirmation are required before any clinical decision.
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div class='info-box'>"
            "⚠️ <b>Clinical disclaimer</b>: This application is a research prototype and screening aid only. "
            "It does not establish a diagnosis and must not be used as a substitute for CT imaging, clinical examination, "
            "or specialist medical assessment."
            "</div>",
            unsafe_allow_html=True
        )

    else:
        st.warning("The antero-posterior diameter cannot be zero.")

else:
    st.markdown(
        "<div class='info-box'>"
        "📌 Upload both photos and enter the landmark coordinates to calculate the result."
        "</div>",
        unsafe_allow_html=True
    )
