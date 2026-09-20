import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from supabase import create_client, Client

# 1. 페이지 기본 설정 (상단 여백 완전 제거 CSS 및 버튼 스타일 적용)
st.set_page_config(page_title="도윤 영어단어 암기장", layout="wide")

# ==========================================
# 여기(8행 이후)에 Supabase 설정 및 사용자 관리 코드를 넣으시면 됩니다!
# ==========================================
SUPABASE_URL = "https://vstetskytidhvqeyxyyi.supabase.co"
SUPABASE_KEY = "sb_publishable_WwjtW2g3-5dHGKOAbXbBNw_2dL5ZU-G"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.sidebar.title("👤 사용자 관리")
user_input_id = st.sidebar.text_input(
    "사용자 ID (닉네임)", 
    value="default_user", 
    help="본인 ID를 입력하고 Enter를 누르면 내 개별 학습 데이터를 불러옵니다."
)

if "current_user_id" not in st.session_state or st.session_state.current_user_id != user_input_id:
    st.session_state.current_user_id = user_input_id
    st.session_state.db_loaded = False

user_id = st.session_state.current_user_id

if not st.session_state.get("db_loaded", False):
    try:
        res = supabase.table("english_user_progress").select("*").eq("user_id", user_id).execute()
        if res.data:
            st.session_state.memorized_words = set(res.data[0].get("memorized_words", []))
        else:
            st.session_state.memorized_words = set()
            supabase.table("english_user_progress").upsert({
                "user_id": user_id,
                "memorized_words": list(st.session_state.memorized_words)
            }).execute()
    except Exception as e:
        if "memorized_words" not in st.session_state:
            st.session_state.memorized_words = set()
    st.session_state.db_loaded = True

def save_user_progress():
    try:
        supabase.table("english_user_progress").upsert({
            "user_id": user_id,
            "memorized_words": list(st.session_state.memorized_words)
        }).execute()
    except Exception as e:
        pass
# ==========================================

st.markdown("""
    <style>
        /* 상단 배경만 투명하게 처리하고 사이드바 버튼은 유지 */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        iframe {
            margin-bottom: -5px !important;
        }
        /* 암기 완료 버튼 커스텀 스타일 */
        .stButton>button {
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

DEFAULT_FILE_PATH = "영단어앱카드제작.txt"

# 2. 세션 상태 초기화
if "cards_db" not in st.session_state:
    st.session_state.cards_db = {}
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "selected_round" not in st.session_state:
    st.session_state.selected_round = "전체 보기"
if "memorized_words" not in st.session_state:
    st.session_state.memorized_words = set() # 암기 완료되어 제외될 단어 집합

# 데이터 파싱 함수 (| 구분자 기준)
def parse_and_load_data(file_content):
    lines = file_content.decode("utf-8", errors="ignore").splitlines()
    added_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split("|")
        # ID|차수|단어|뜻|동의어|영문예문|한글해석
        if len(parts) >= 7:
            c_id = parts[0].strip()
            c_round = parts[1].strip()
            c_word = parts[2].strip()
            c_meaning = parts[3].strip()
            c_synonym = parts[4].strip()
            c_ex_en = parts[5].strip()
            c_ex_kr = parts[6].strip()
            
            if c_word not in st.session_state.cards_db:
                st.session_state.cards_db[c_word] = {
                    "id": c_id,
                    "round": c_round,
                    "word": c_word,
                    "meaning": c_meaning,
                    "synonym": c_synonym,
                    "example_en": c_ex_en,
                    "example_kr": c_ex_kr
                }
                added_count += 1
    return added_count

# 3D Flip 카드 HTML 템플릿
def generate_card_html(card, is_mini=False):
    if is_mini:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: transparent;
                font-family: system-ui, -apple-system, sans-serif;
            }}
            .flip-card {{
                background-color: transparent;
                width: 100%;
                height: 125px;
                perspective: 600px;
                cursor: pointer;
            }}
            .flip-card-inner {{
                position: relative;
                width: 100%;
                height: 100%;
                text-align: center;
                transition: transform 0.6s;
                transform-style: preserve-3d;
            }}
            .flip-card.flipped .flip-card-inner {{
                transform: rotateY(180deg);
            }}
            .flip-card-front, .flip-card-back {{
                position: absolute;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                border-radius: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 8px;
                box-sizing: border-box;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
            }}
            .flip-card-front {{
                background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
                border: 2px solid #cbd5e1;
                color: #0f172a;
            }}
            .flip-card-back {{
                background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
                border: 2px solid #38bdf8;
                color: #0369a1;
                transform: rotateY(180deg);
            }}
            .card-meta {{
                font-size: 0.75rem;
                font-weight: 600;
                color: #64748b;
                margin-bottom: 4px;
            }}
            .word-en {{
                font-size: 1.35rem;
                font-weight: 800;
                word-break: break-word;
            }}
            .word-kr {{
                font-size: 1.15rem;
                font-weight: 700;
                word-break: break-word;
            }}
            .click-hint {{
                font-size: 0.65rem;
                color: #94a3b8;
                margin-top: 4px;
            }}
        </style>
        </head>
        <body>
            <div class="flip-card" onclick="this.classList.toggle('flipped')">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <div class="card-meta">#{card.get('id', '')} | {card.get('round', '')}차</div>
                        <div class="word-en">{card.get('word', '')}</div>
                        <div class="click-hint">click 🔍</div>
                    </div>
                    <div class="flip-card-back">
                        <div class="word-kr">{card.get('meaning', '')}</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: transparent;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: system-ui, -apple-system, sans-serif;
        }}
        .flip-card {{
            background-color: transparent;
            width: 560px;
            height: 300px;
            perspective: 1000px;
            cursor: pointer;
        }}
        .flip-card-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
            transform-style: preserve-3d;
        }}
        .flip-card.flipped .flip-card-inner {{
            transform: rotateY(180deg);
        }}
        .flip-card-front, .flip-card-back {{
            position: absolute;
            width: 100%;
            height: 100%;
            -webkit-backface-visibility: hidden;
            backface-visibility: hidden;
            border-radius: 18px;
            padding: 24px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }}
        .flip-card-front {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 2px solid #3b82f6;
            color: #ffffff;
        }}
        .flip-card-back {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border: 2px solid #818cf8;
            color: #ffffff;
            transform: rotateY(180deg);
        }}
        </style>
        </head>
        <body>
        <div class="flip-card" id="card_{card['id']}">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px;">
                        <span>ID: {card['id']}</span>
                        <span style="background: #1e3a8a; padding: 2px 8px; border-radius: 6px; color: #93c5fd;">{card['round']}</span>
                    </div>
                    <div style="text-align: center; margin: auto 0;">
                        <div style="font-size: 44px; font-weight: 800; color: #60a5fa; letter-spacing: 0.5px;">{card['word']}</div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b;">
                        <span>👆 카드를 클릭하면 뒤집힙니다</span>
                        <span>단어 카드</span>
                    </div>
                </div>
                <div class="flip-card-back">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; color: #a5b4fc; border-bottom: 1px solid #312e81; padding-bottom: 8px;">
                        <span>ID: {card['id']} | <strong>{card['word']}</strong></span>
                        <span style="background: #312e81; padding: 2px 8px; border-radius: 6px; color: #c7d2fe;">{card['round']}</span>
                    </div>
                    <div style="margin: auto 0; overflow-y: auto;">
                        <div style="font-size: 24px; font-weight: 700; color: #38bdf8; margin-bottom: 8px;">📌 {card['meaning']}</div>
                        <div style="font-size: 13px; color: #cbd5e1; margin-bottom: 12px; background: rgba(255,255,255,0.1); display: inline-block; padding: 4px 10px; border-radius: 6px;">🔗 동의어: {card['synonym']}</div>
                        <div style="margin-top: 6px; background: rgba(0,0,0,0.25); padding: 10px; border-radius: 8px;">
                            <div style="font-size: 14px; color: #f1f5f9; line-height: 1.4;">🗣️ {card['example_en']}</div>
                            <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">💬 {card['example_kr']}</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b;">
                        <span>👆 다시 클릭하면 앞면으로 뒤집힙니다</span>
                        <span>뜻 및 예문</span>
                    </div>
                </div>
            </div>
        </div>
        <script>
            document.getElementById('card_{card['id']}').addEventListener('click', function() {{
                this.classList.toggle('flipped');
            }});
        </script>
        </body>
        </html>
        """

# 기본 txt 파일 자동 로드
if os.path.exists(DEFAULT_FILE_PATH):
    with open(DEFAULT_FILE_PATH, "rb") as f:
        st.session_state.cards_db.clear()
        parse_and_load_data(f.read())

# ---------------------------------------------------------
# 사이드바 (Sidebar) 구성
# ---------------------------------------------------------
st.sidebar.title("🎴 영어단어 암기장")

all_rounds = sorted(list(set([v["round"] for v in st.session_state.cards_db.values()])))
round_options = ["전체 보기"] + all_rounds

st.sidebar.markdown("### 📚 차수 선택")
selected_round_choice = st.sidebar.selectbox(
    "학습할 차수를 선택하세요:",
    round_options,
    index=round_options.index(st.session_state.selected_round) if st.session_state.selected_round in round_options else 0,
    key="round_select_box"
)

if selected_round_choice != st.session_state.selected_round:
    st.session_state.selected_round = selected_round_choice
    st.session_state.current_index = 0

st.sidebar.markdown("---")

# 암기 완료 리셋 관리 기능 추가
st.sidebar.markdown("### 🎯 암기 상태 관리")
memorized_cnt = len(st.session_state.memorized_words)
st.sidebar.write(f"✅ 완료 처리된 단어: **{memorized_cnt}** 개")

if st.sidebar.button("🔄 제외된 단어 모두 복원", use_container_width=True):
    st.session_state.memorized_words.clear()
    save_user_progress()  # <--- 이 줄을 추가해 주세요!
    st.sidebar.success("모든 단어가 다시 학습 대상에 포함되었습니다!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ 메뉴 이동")
data_menu = st.sidebar.radio(
    "메뉴를 선택하세요:",
    ["🖼️ 회차별 전체 모아보기 (5열)", "🎴 개별 플래시카드 학습", "📄 원본 데이터", "📁 데이터 업로드"],
    index=0
)

# ---------------------------------------------------------
# 페이지 1: 회차별 전체 모아보기 (암기 제외 기능 적용)
# ---------------------------------------------------------
if data_menu == "🖼️ 회차별 전체 모아보기 (5열)":
    if not st.session_state.cards_db:
        st.warning("등록된 단어가 없습니다.")
    else:
        # 암기 완료 단어 제외 필터링
        if st.session_state.selected_round == "전체 보기":
            target_cards = [v for k, v in st.session_state.cards_db.items() if k not in st.session_state.memorized_words]
        else:
            target_cards = [v for k, v in st.session_state.cards_db.items() if v["round"] == st.session_state.selected_round and k not in st.session_state.memorized_words]

        if len(target_cards) == 0:
            st.balloons()
            st.success("🎉 선택한 차수의 모든 단어를 암기 완료했습니다! (사이드바에서 '제외된 단어 모두 복원'을 누르면 다시 공부할 수 있습니다)")
        else:
            cols_per_row = 5
            for i in range(0, len(target_cards), cols_per_row):
                cols = st.columns(cols_per_row)
                row_cards = target_cards[i:i+cols_per_row]
                
                for idx, card in enumerate(row_cards):
                    with cols[idx]:
                        c_html = generate_card_html(card, is_mini=True)
                        components.html(c_html, height=130)
                        
                        # 카드 밑에 '암기 완료' 버튼 추가
                        if st.button("완료 ✅", key=f"btn_m_{card['word']}", use_container_width=True):
                            st.session_state.memorized_words.add(card['word'])
                            save_user_progress()
                            st.rerun()

# ---------------------------------------------------------
# 페이지 2: 개별 플래시카드 학습 (암기 제외 기능 적용)
# ---------------------------------------------------------
elif data_menu == "🎴 개별 플래시카드 학습":
    st.markdown("<h3 style='font-size: 1.3rem; margin-top: -10px; margin-bottom: 10px;'>🎴 개별 플래시카드 학습</h3>", unsafe_allow_html=True)
    
    if not st.session_state.cards_db:
        st.warning("등록된 단어가 없습니다.")
    else:
        # 암기 완료 단어 제외 필터링
        if st.session_state.selected_round == "전체 보기":
            filtered_words = [w for w in st.session_state.cards_db.keys() if w not in st.session_state.memorized_words]
        else:
            filtered_words = [w for w, v in st.session_state.cards_db.items() if v["round"] == st.session_state.selected_round and w not in st.session_state.memorized_words]

        total_words = len(filtered_words)

        if total_words == 0:
            st.balloons()
            st.success("🎉 선택한 차수의 모든 단어를 암기 완료했습니다!")
        else:
            if st.session_state.current_index >= total_words:
                st.session_state.current_index = 0

            if "selected_word_key" not in st.session_state or st.session_state.selected_word_key not in filtered_words:
                st.session_state.selected_word_key = filtered_words[st.session_state.current_index]

            def on_word_change():
                chosen = st.session_state.word_select_box
                st.session_state.selected_word_key = chosen
                st.session_state.current_index = filtered_words.index(chosen)

            col_select, col_mem = st.columns([3, 1])
            with col_select:
                st.selectbox(
                    f"학습할 단어 선택 ({st.session_state.selected_round} - 남은 단어: {total_words}개):",
                    filtered_words,
                    index=st.session_state.current_index,
                    key="word_select_box",
                    on_change=on_word_change
                )
            with col_mem:
                st.write("") # 간격 조정
                st.write("")
                if st.button("이 단어 암기 완료 ✅", use_container_width=True):
                    st.session_state.memorized_words.add(st.session_state.selected_word_key)
                    save_user_progress()
                    if st.session_state.current_index >= len(filtered_words) - 1:
                        st.session_state.current_index = 0
                    st.rerun()

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("◀ 이전 단어", use_container_width=True):
                    st.session_state.current_index = (st.session_state.current_index - 1) % total_words
                    st.session_state.selected_word_key = filtered_words[st.session_state.current_index]
                    st.rerun()
            with col2:
                if st.button("다음 단어 ▶", use_container_width=True):
                    st.session_state.current_index = (st.session_state.current_index + 1) % total_words
                    st.session_state.selected_word_key = filtered_words[st.session_state.current_index]
                    st.rerun()

            card = st.session_state.cards_db[st.session_state.selected_word_key]
            card_html = generate_card_html(card, is_mini=False)
            components.html(card_html, height=310)

# ---------------------------------------------------------
# 페이지 3: 원본 데이터
# ---------------------------------------------------------
elif data_menu == "📄 원본 데이터":
    st.title("📄 원본 데이터 관리")
    if st.session_state.cards_db:
        df = pd.DataFrame(st.session_state.cards_db.values())
        st.metric(label="총 등록된 단어 수", value=f"{len(df)} 개")
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 페이지 4: 데이터 업로드
# ---------------------------------------------------------
elif data_menu == "📁 데이터 업로드":
    st.title("📁 데이터 추가 업로드")
    uploaded_file = st.file_uploader("txt 파일 선택", type=["txt"])
    if uploaded_file is not None:
        added = parse_and_load_data(uploaded_file.read())
        if added > 0:
            st.success(f"새로운 단어 {added}개가 성공적으로 추가되었습니다!")
            st.rerun()