import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# 1. 페이지 기본 설정 (상단 여백 완전 제거 CSS)
st.set_page_config(page_title="도윤 영어단어 암기장", layout="wide")

# 상단 여백 확보 CSS (Deploy 버튼 밑으로 밀기)
st.markdown("""
    <style>
        .block-container {
            padding-top: 4rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* iframe 간격 최소화 */
        iframe {
            margin-bottom: -10px !important;
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

# 3D Flip 카드 HTML 템플릿 (10열 배치용 컴팩트 사이즈)
def generate_card_html(card, is_mini=False):
    if is_mini:
        # 가로 10개 전용 초미니 템플릿
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
            height: 95px;
            perspective: 600px;
            cursor: pointer;
        }}
        .flip-card-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            transition: transform 0.4s ease;
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
            border-radius: 6px;
            padding: 5px 6px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }}
        .flip-card-front {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #3b82f6;
            color: #ffffff;
        }}
        .flip-card-back {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border: 1px solid #818cf8;
            color: #ffffff;
            transform: rotateY(180deg);
        }}
        </style>
        </head>
        <body>
        <div class="flip-card" id="card_{card['id']}">
            <div class="flip-card-inner">
                <!-- 앞면 -->
                <div class="flip-card-front">
                    <div style="display: flex; justify-content: space-between; font-size: 9px; color: #94a3b8;">
                        <span>#{card['id']}</span>
                        <span style="color: #93c5fd;">{card['round']}</span>
                    </div>
                    <div style="text-align: center; margin: auto 0;">
                        <div style="font-size: 13px; font-weight: 700; color: #60a5fa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{card['word']}</div>
                    </div>
                    <div style="font-size: 7px; color: #475569; text-align: right;">click 🔄</div>
                </div>
                <!-- 뒷면 -->
                <div class="flip-card-back">
                    <div style="font-size: 9px; color: #a5b4fc; font-weight: bold; border-bottom: 1px solid #312e81; padding-bottom: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{card['word']}</div>
                    <div style="margin: auto 0; overflow: hidden;">
                        <div style="font-size: 10px; font-weight: 700; color: #38bdf8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{card['meaning']}</div>
                        <div style="font-size: 8px; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{card['synonym']}</div>
                    </div>
                    <div style="font-size: 7px; color: #475569; text-align: right;">back ↩</div>
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
    else:
        # 일반 개별 학습 카드
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
            height: 320px;
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
st.sidebar.markdown("### ⚙️ 메뉴 이동")
data_menu = st.sidebar.radio(
    "메뉴를 선택하세요:",
    ["🖼️ 회차별 전체 모아보기 (10열)", "🎴 개별 플래시카드 학습", "📄 원본 데이터", "📁 데이터 업로드"],
    index=0
)

# ---------------------------------------------------------
# 페이지 1: 회차별 전체 모아보기 (상단 제목 완전제거 & 가로 10열)
# ---------------------------------------------------------
if data_menu == "🖼️ 회차별 전체 모아보기 (10열)":
    if not st.session_state.cards_db:
        st.warning("등록된 단어가 없습니다.")
    else:
        if st.session_state.selected_round == "전체 보기":
            target_cards = list(st.session_state.cards_db.values())
        else:
            target_cards = [v for v in st.session_state.cards_db.values() if v["round"] == st.session_state.selected_round]

        if len(target_cards) == 0:
            st.warning("단어가 없습니다.")
        else:
            # 가로 10열(Columns) 바둑판 배치
            cols_per_row = 10
            for i in range(0, len(target_cards), cols_per_row):
                cols = st.columns(cols_per_row)
                row_cards = target_cards[i:i+cols_per_row]
                
                for idx, card in enumerate(row_cards):
                    with cols[idx]:
                        c_html = generate_card_html(card, is_mini=True)
                        components.html(c_html, height=105)

# ---------------------------------------------------------
# 페이지 2: 개별 플래시카드 학습
# ---------------------------------------------------------
elif data_menu == "🎴 개별 플래시카드 학습":
    st.title("🎴 개별 플래시카드 학습")
    
    if not st.session_state.cards_db:
        st.warning("등록된 단어가 없습니다.")
    else:
        if st.session_state.selected_round == "전체 보기":
            filtered_words = list(st.session_state.cards_db.keys())
        else:
            filtered_words = [w for w, v in st.session_state.cards_db.items() if v["round"] == st.session_state.selected_round]

        total_words = len(filtered_words)

        if total_words == 0:
            st.warning("선택한 차수에 단어가 없습니다.")
        else:
            if st.session_state.current_index >= total_words:
                st.session_state.current_index = 0

            if "selected_word_key" not in st.session_state or st.session_state.selected_word_key not in filtered_words:
                st.session_state.selected_word_key = filtered_words[st.session_state.current_index]

            def on_word_change():
                chosen = st.session_state.word_select_box
                st.session_state.selected_word_key = chosen
                st.session_state.current_index = filtered_words.index(chosen)

            st.selectbox(
                f"학습할 단어 선택 ({st.session_state.selected_round}):",
                filtered_words,
                index=st.session_state.current_index,
                key="word_select_box",
                on_change=on_word_change
            )

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
            components.html(card_html, height=350)

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