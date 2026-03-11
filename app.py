import streamlit as st
import pandas as pd
from data import STANDS
import os
import plotly.graph_objects as go
import importlib
import data
from PIL import Image
import base64

# 常に最新のデータを読み込むための処理
importlib.reload(data)
from data import STANDS

# セッション状態の初期化
if 'detail_view_mode' not in st.session_state:
    st.session_state.detail_view_mode = "tarot"

# アップロード用ディレクトリの作成
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ページ設定
st.set_page_config(
    page_title="JOJO Stand Dex - Visual Edition",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 画像取得・Base64変換ヘルパー
def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def get_dual_images(stand_id, default_img):
    # ウェブ環境（Streamlit Cloud）対応：ローカルパスを排除
    tarot_img = None 
    if os.path.exists("tarot_back_design.png"):
        tarot_img = "tarot_back_design.png"
    elif os.path.exists("tarot_back_design.jpg"):
        tarot_img = "tarot_back_design.jpg"

    stand_img = default_img

    # カレントディレクトリのファイルを確認
    try:
        files = os.listdir(".")
    except:
        files = []
    
    def normalize(s):
        # 拡張子を除いたファイル名を正規化
        base = os.path.splitext(s)[0]
        return base.lower().replace(" ", "").replace("_", "").replace("-", "").replace("[", "").replace("]", "")

    stand_id_norm = normalize(stand_id)
    # 名称の揺れに対応 (単数形など) 
    id_words = [normalize(w).rstrip("s") for w in stand_id.split("_") if len(w) > 3]

    SPECIAL_MAPPINGS = {
        "death_thirteen": ["death13", "death"],
        "dark_blue_moon": ["darkbruemoon", "darkblue", "moon"],
        "ebony_devil": ["ebonydevil", "devil", "ebony"],
        "silver_chariots": ["chariot", "silverchariot", "silva"],
        "hierophant_green": ["hierophant", "kakyoin"],
        "star_platinum": ["star", "ster", "platinam"],
        "hermit_purple": ["hermit", "harmit", "parple"],
        "the_fool": ["fool", "iggy"],
        "the_world": ["world", "warld"],
        "judgement": ["judgement", "judgment"],
        "high_priestess": ["highpriestess", "hipriest"],
        "tower_of_gray": ["tower"],
        "lovers": ["lover"],
        "magicians_red": ["magician", "magiciansred"],
        "wheel_of_fortune": ["wheeloffortune", "wheel"],
        "justice": ["justice"],
        "yellow_temperance": ["temperance"],
        "emperor": ["emperor"],
        "empress": ["empress"],
        "sun": ["sun"],
        "thoth": ["tohth", "thoth"],
        "geb": ["geb"],
        "khnum": ["khnum"]
    }
    
    extra_keywords = SPECIAL_MAPPINGS.get(stand_id, [])

    # 一致するファイルを収集
    found_tarots = []
    found_stands = []

    for f in files:
        f_lower = f.lower()
        if not f_lower.endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
            
        f_norm = normalize(f)
        
        # マッチング判定
        has_id = (stand_id_norm in f_norm)
        has_word = any(w in f_norm for w in id_words)
        has_extra = any(normalize(kw) in f_norm for kw in extra_keywords)
        
        if has_id or has_word or has_extra:
            # 1. OVATarot ファイル (最優先タロット表面)
            if "ovatarot" in f_lower:
                found_tarots.append(f)
            # 2. "THE " で始まるファイル (従来タロット/またはスタンド画像)
            elif f_lower.startswith("the") and "[tarot]" in f_lower:
                found_tarots.append(f)
            elif f_lower.startswith("the") and "tarot_back" not in f_lower:
                # [tarot]がなくても、OVAタロットが見つかっていない間は候補にする
                found_tarots.append(f)
            # 3. それ以外 (スタンド本体画像)
            else:
                found_stands.append(f)

    # 決定ロジック
    # タロット面: OVATarotを絶対優先、なければ他のTHE...
    ova_only = [f for f in found_tarots if "ovatarot" in f.lower()]
    if ova_only:
        tarot_img = ova_only[0]
    elif found_tarots:
        tarot_img = found_tarots[0]

    # スタンド面: [tarot]や[ovatarot]が含まれないファイルを優先
    final_stand_candidates = [f for f in found_stands if "ovatarot" not in f.lower()]
    
    # PNG（透過）があれば最優先
    png_stands = [f for f in final_stand_candidates if f.lower().endswith(".png")]
    if png_stands:
        stand_img = png_stands[0]
    elif final_stand_candidates:
        stand_img = final_stand_candidates[0]
    elif found_stands:
        stand_img = found_stands[0]
    elif tarot_img and stand_img == default_img:
        # どうしても画像がない場合は一覧でタロットを表示
        stand_img = tarot_img

    # 特例 (アップロードや個人設定)
    for ext in [".webp", ".png", ".jpg", ".jpeg"]:
        custom_path = os.path.join(UPLOAD_DIR, f"{stand_id}{ext}")
        if os.path.exists(custom_path):
            stand_img = custom_path
            break
            
    if stand_id == "hierophant_green":
        if os.path.exists("kakyoin.png"): stand_img = "kakyoin.png"
        elif os.path.exists("kakyoin.jpg"): stand_img = "kakyoin.jpg"
    
    return tarot_img, stand_img

# カスタムCSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #ffffff;
    }

    .stApp {
        background: transparent;
    }

    /* タイトルセクション */
    .hero-container {
        text-align: center;
        padding: 40px 20px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 30px;
        border: 1px solid rgba(255, 215, 0, 0.2);
    }

    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #FFD700, #FFA500, #FF4500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* 画像ラッパー */
    .stand-image-wrapper {
        width: 100%;
        height: 240px; /* カード内の画像高さを固定 */
        overflow: hidden;
        border-radius: 12px;
        margin-bottom: 15px;
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .stand-image-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: top center;
        transition: transform 0.5s ease;
    }
    .stand-card:hover .stand-image-wrapper img {
        transform: scale(1.1);
    }

    /* 詳細画面用画像ラッパー */
    .detail-image-wrapper {
        width: 100%;
        height: 480px;
        overflow: hidden;
        border-radius: 20px;
        border: 2px solid gold;
        background: rgba(0,0,0,0.4);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .detail-image-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: contain; /* coverからcontainに変更：画像が枠内に収まるように */
        padding: 10px;       /* 枠線に密着しすぎないよう少し余白を追加 */
    }

    /* スタンドカード */
    .stand-card {
        background: rgba(255, 255, 255, 0.07);
        border-radius: 15px;
        padding: 20px;
        border-left: 5px solid gold;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 15px;
    }

    .stand-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(255, 215, 0, 0.15);
        background: rgba(255, 255, 255, 0.12);
    }

    .stand-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #fff;
    }

    .stand-user {
        font-size: 0.9rem;
        color: #ffd700;
        margin-bottom: 5px;
    }

    .tarot-badge {
        font-size: 0.75rem;
        color: #e0e0e0;
        background: rgba(0, 0, 0, 0.3);
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 8px;
        border: 1px solid rgba(255, 215, 0, 0.3);
    }

    .param-badge {
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.15);
        display: inline-block;
    }

    .value-A { color: #f44336; font-weight: bold; }
    .value-B { color: #ffeb3b; font-weight: bold; }
    .value-C { color: #4caf50; font-weight: bold; }
    .value-D { color: #2196f3; font-weight: bold; }
    .value-E { color: #9e9e9e; font-weight: bold; }

    /* タロット背面プレースホルダー */
    .tarot-back-placeholder {
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, #1a1a1a 10%, #4a3c10 50%, #1a1a1a 90%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: gold;
        border: 4px double gold;
        border-radius: 12px;
        position: relative;
    }
    .tarot-back-placeholder::before {
        content: "TAROT";
        font-size: 2.5rem;
        font-weight: 900;
        letter-spacing: 5px;
        opacity: 0.6;
    }

    /* 切り替えボタンの特殊スタイル */
    .stButton > button.toggle-btn {
        background-color: gold !important;
        color: #000 !important;
        font-weight: 900 !important;
        border: 2px solid #fff !important;
        border-radius: 30px !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4) !important;
    }

    /* BGMプレイヤーのスタイル */
    .bgm-container {
        background: rgba(255, 215, 0, 0.1);
        padding: 15px;
        border-radius: 12px;
        border: 2px solid gold;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
    }
    .bgm-container audio {
        width: 100%;
        height: 35px;
        margin-top: 10px;
        filter: sepia(100%) saturate(200%) hue-rotate(10deg); /* 金色に合わせるための色フィルタ */
    }
</style>
""", unsafe_allow_html=True)

# レーダーチャート作成関数
def create_radar_chart(params, color):
    mapping = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
    categories = ['破壊力', 'スピード', '射程距離', '持続力', '精密動作性', '成長性']
    values = [mapping.get(params.get(cat, 'E'), 1) for cat in categories]
    
    categories_plot = categories + [categories[0]]
    values_plot = values + [values[0]]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_plot,
        theta=categories_plot,
        fill='toself',
        line_color=color,
        fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.3,)}",
        name='Parameters'
    ))
    
    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 5],
                "tickvals": [1, 2, 3, 4, 5],
                "ticktext": ['E', 'D', 'C', 'B', 'A'],
                "gridcolor": 'rgba(255, 255, 255, 0.2)',
                "linecolor": 'rgba(255, 255, 255, 0.2)',
                "tickfont": {"size": 10, "color": 'gray'}
            },
            "angularaxis": {
                "gridcolor": 'rgba(255, 255, 255, 0.2)',
                "linecolor": 'rgba(255, 255, 255, 0.2)',
                "tickfont": {"size": 12, "color": 'white'}
            },
            "bgcolor": 'rgba(0,0,0,0)'
        },
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin={"l": 40, "r": 40, "t": 30, "b": 30},
        height=300
    )
    return fig

# ヒーローセクション
st.markdown("""
<div class="hero-container">
    <div class="hero-title">STARDUST CRUSADERS</div>
    <div class="hero-subtitle">ジョジョの奇妙な冒険 第3部 スタンド大図鑑</div>
</div>
""", unsafe_allow_html=True)

# スタンド表示関数
def display_stands(stands_list):
    if not stands_list:
        st.warning("条件に一致するスタンドは見わ見つかりませんでした。")
        return

    cols = st.columns(3)
    for idx, stand in enumerate(stands_list):
        with cols[idx % 3]:
            # 一覧画面では「スタンド画像」を優先表示
            _, stand_img = get_dual_images(stand["id"], stand.get("image"))
            img_b64 = get_image_base64(stand_img)
            
            if img_b64:
                st.markdown(f"""
                <div class="stand-image-wrapper">
                    <img src="data:image/png;base64,{img_b64}">
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="stand-image-wrapper" style="background: {stand['color']}; opacity: 0.5;">
                    <span style="font-size: 3rem; font-weight: 900; color: white;">{stand['name'][0]}</span>
                </div>
                """, unsafe_allow_html=True)

            # カード表示
            tarot_info = stand.get("tarot", "なし")
            params_short = "".join([
                f'<span class="param-badge" style="margin-right:2px;">{k[0]}<span class="value-{v}">{v}</span></span>'
                for k, v in stand["parameters"].items()
            ])
            
            st.markdown(f"""
            <div class="stand-card" style="border-left-color: {stand['color']};">
                <div class="tarot-badge">🎴 {tarot_info}</div>
                <div class="stand-name">{stand['name']}</div>
                <div class="stand-user">本 体：{stand['user']}</div>
                <div style="margin-top: 5px; height: 30px; overflow: hidden;">{params_short}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"詳細: {stand['name']}", key=f"btn_{stand['id']}"):
                st.session_state.selected_stand_id = stand['id']
                st.rerun()

# サイドバー
st.sidebar.title("🌌 検索・設定")
search_query = st.sidebar.text_input("名前・本体で検索", "").lower()

if st.sidebar.button("データを強制再読込"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# BGMセクション
bgm_path = "jojomusic.mp3"
if os.path.exists(bgm_path):
    import base64
    with open(bgm_path, "rb") as f:
        bgm_data = base64.b64encode(f.read()).decode()
    
    html_bgm = f"""
    <div class="bgm-container">
        <div style="color: gold; font-weight: bold; margin-bottom: 5px;">🎵 BGM: STAND PROUD</div>
        <audio controls loop>
            <source src="data:audio/mp3;base64,{bgm_data}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    </div>
    """
    st.sidebar.markdown(html_bgm, unsafe_allow_html=True)
else:
    st.sidebar.warning("BGMファイルが見つかりません")

# カテゴリ定義
CATEGORIES = {
    "ジョースター一行": ["star_platinum", "magicians_red", "hermit_purple", "hierophant_green", "silver_chariots", "the_fool"],
    "タロットの刺客(1)": ["tower_of_gray", "dark_blue_moon", "strength", "ebony_devil", "yellow_temperance", "hanged_man", "emperor", "empress"],
    "タロットの刺客(2)": ["wheel_of_fortune", "justice", "lovers", "sun", "death_thirteen", "judgement", "high_priestess"],
    "エジプト9栄神": ["geb", "khnum", "thoth", "anubis", "bastet", "sethan", "osiris", "horus", "atum"],
    "DIOの館": ["tenore_sax", "cream", "the_world"]
}

if search_query:
    filtered_stands = [s for s in STANDS if search_query in s["name"].lower() or search_query in s["user"].lower()]
    display_stands(filtered_stands)
else:
    tabs = st.tabs(list(CATEGORIES.keys()))
    for i, (cat_name, stand_ids) in enumerate(CATEGORIES.items()):
        with tabs[i]:
            cat_stands = [s for s in STANDS if s["id"] in stand_ids]
            display_stands(cat_stands)

# 詳細表示
if 'selected_stand_id' in st.session_state:
    # 新しいスタンドが選ばれたら表示モードを初期化
    if 'last_selected_id' not in st.session_state or st.session_state.last_selected_id != st.session_state.selected_stand_id:
        st.session_state.detail_view_mode = "tarot"
        st.session_state.last_selected_id = st.session_state.selected_stand_id

    st.markdown("---")
    selected = next((s for s in STANDS if s["id"] == st.session_state.selected_stand_id), None)
    
    if selected:
        if st.button("× 図鑑を閉じる"):
            del st.session_state.selected_stand_id
            st.rerun()

        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.subheader(selected["name"])
            
            # 画像パスの準備 (タロット面とスタンド面)
            tarot_path, stand_img_path = get_dual_images(selected["id"], selected.get("image"))
            
            # モード切替ボタン
            stand_name_only = selected["name"].split("（")[0]
            if st.session_state.detail_view_mode == "tarot":
                btn_label = f"🎴 {stand_name_only}を出現させる！"
            else:
                btn_label = "🃏 タロットカードに戻す"
                
            if st.button(btn_label, key=f"toggle_{selected['id']}", use_container_width=True):
                st.session_state.detail_view_mode = "stand" if st.session_state.detail_view_mode == "tarot" else "tarot"
                st.rerun()

            # 画像表示エリア
            if st.session_state.detail_view_mode == "tarot":
                # 初期表示（タロット面）
                img_b64 = get_image_base64(tarot_path)
                if img_b64:
                    st.markdown(f'<div class="detail-image-wrapper"><img src="data:image/png;base64,{img_b64}"></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="detail-image-wrapper"><div class="tarot-back-placeholder"></div></div>', unsafe_allow_html=True)
                
                st.info(f"👆 ボタンを押して、{stand_name_only}を呼び出そう！")
            else:
                # 切り替え後（出現後）
                img_b64 = get_image_base64(stand_img_path)
                if img_b64:
                    st.markdown(f'<div class="detail-image-wrapper"><img src="data:image/png;base64,{img_b64}"></div>', unsafe_allow_html=True)
                else:
                    st.warning("スタンド画像が見つかりません。")
                
                st.success(f"{stand_name_only}、出現！！")
            st.write("📷 **カスタム画像を設定**")
            uploaded_file = st.file_uploader(f"{selected['name']}の画像をアップロード", type=["png", "jpg", "jpeg"], key=f"uploader_{selected['id']}")
            
            if uploaded_file is not None:
                ext = uploaded_file.name.split(".")[-1]
                save_path = os.path.join(UPLOAD_DIR, f"{selected['id']}.{ext}")
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("画像を保存しました！")
                st.rerun()
                
        with c2:
            st.markdown(f"### **本体: {selected['user']}**")
            st.markdown(f"""
            <div style="background: rgba(255, 215, 0, 0.1); padding: 15px; border-radius: 10px; border: 1px solid gold; margin-bottom: 20px;">
                <h4 style="margin: 0; color: gold;">🎴 対応タロット</h4>
                <p style="font-size: 1.5rem; font-weight: 900; margin: 10px 0 0 0;">{selected.get('tarot', 'なし')}</p>
            </div>
            """, unsafe_allow_html=True)

            st.info(f"**能力:** {selected['ability']}")
            radar_fig = create_radar_chart(selected["parameters"], selected["color"])
            st.plotly_chart(radar_fig, use_container_width=True)
