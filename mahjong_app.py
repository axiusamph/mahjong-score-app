import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import ast

# Google Sheets 설정
SHEET_NAME = "mahjong_scores"
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gcp_service_account"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(credentials)
sheet = client.open(SHEET_NAME).sheet1

# 유틸: 구글 시트에서 기존 데이터 불러오기
def load_game_history():
    records = sheet.get_all_records()
    history = []
    for r in records:
        try:
            game_data = ast.literal_eval(r['game'])  # 문자열 → 리스트(dict)
            history.append(game_data)
        except:
            pass
    return history

# 유틸: 게임 결과 저장
def save_game_to_sheet(game_result, game_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 각 플레이어 정보 저장
    sheet.append_row([game_id, str(game_result), timestamp])

# 새로고침 및 세션을 새로 시작할 때마다 시트에서 데이터를 불러오는 로직
if 'game_history' not in st.session_state:
    # 게임 기록을 시트에서 불러오고 세션 상태에 저장
    st.session_state.game_history = load_game_history()
    st.session_state.players = {}
    # 누적 계산
    for game in st.session_state.game_history:
        for entry in game:
            name = entry['name']
            score = entry['score']
            rating = entry['rating']
            if name not in st.session_state.players:
                st.session_state.players[name] = {'score': 0, 'rating': 0}
            st.session_state.players[name]['score'] += score
            st.session_state.players[name]['rating'] += rating

# 계산 함수
def calculate_rating(rank, score, okka, uma_n, uma_m):
    if okka == "있음":
        first_bonus = 20000
        returning_score = 30000
    else:
        first_bonus = 0
        returning_score = 25000

    if rank == 1:
        return (score + first_bonus - returning_score) / 1000 + uma_m
    elif rank == 2:
        return (score - returning_score) / 1000 + uma_n
    elif rank == 3:
        return (score - returning_score) / 1000 - uma_n
    elif rank == 4:
        return (score - returning_score) / 1000 - uma_m
    else:
        return score / 1000

# UI 시작
st.title("🀄 팀선비 마작 대회 '녹일색' 기록기")
st.markdown("문제 발생시 김시유에게 연락 주세요. api exp: 6/28/25")

# 새 게임 입력
with st.expander("게임 입력", expanded=False):
    with st.form("game_form"):
        st.subheader("✒️ 새 게임 입력")
    
        # 비밀번호 입력란 추가
        password = st.text_input("비밀번호를 입력하세요", type="password")
    
        okka = st.selectbox("오카 설정", options=["있음", "없음"], index=0)
        uma_n = st.number_input("3등이 2등에게 주는 승점 (N)", value=10)
        uma_m = st.number_input("4등이 1등에게 주는 승점 (M)", value=20)
    
        names, scores = [], []
        for i in range(4):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input(f"{i+1}등 플레이어 이름", key=f"name_{i}")
            with col2:
                score = st.number_input(f"{i+1}등 점수", key=f"score_{i}", step=100)
            names.append(name)
            scores.append(score)
    
        submitted = st.form_submit_button("게임 결과 저장")
        st.markdown("점수가 같지 않다면 자동으로 등수를 조정합니다.")

if submitted:
    # 비밀번호 확인
    if password != "0916":
        st.error("❌ 비밀번호가 틀렸습니다.")
    else:
        # 게임 결과 계산
        game_data = sorted(zip(names, scores), key=lambda x: x[1], reverse=True)

        game_result = []
        for rank, (name, score) in enumerate(game_data, 1):
            rating = calculate_rating(rank, score, okka, uma_n, uma_m)
            if name not in st.session_state.players:
                st.session_state.players[name] = {'score': 0, 'rating': 0}
            st.session_state.players[name]['score'] += score
            st.session_state.players[name]['rating'] += rating
            game_result.append({'name': name, 'score': score, 'rank': rank, 'rating': round(rating, 2)})

        # 새로운 게임 기록 추가
        st.session_state.game_history.append(game_result)
        
        # 게임 ID 설정
        game_id = len(st.session_state.game_history)

        # 게임 결과를 시트에 저장
        save_game_to_sheet(game_result, game_id)
        
        st.success("✅ 게임 결과가 저장되었습니다.")

#누적 승점 출력
if st.session_state.players:
    st.subheader("🏆 누적 승점 결과")

    # 데이터 생성
    df = pd.DataFrame([
        {"이름": name, "누적 승점": round(data["rating"], 1)}
        for name, data in st.session_state.players.items()
    ])

    # 정렬
    df = df.sort_values(by="누적 승점", ascending=False).reset_index(drop=True)

    # 🥇🥈🥉 이모지 추가 (iloc 사용)
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    df["이름"] = [f"{row['이름']} {medals[i]}" if i in medals else row["이름"] for i, row in df.iterrows()]
    
    # 스타일 함수 정의
    def style_row(row):
        rating = row["누적 승점"]
        name_style = ""
        rating_style = ""

        if rating > 0:
            rating_style = "color: #2e8b57"  # 초록
        elif rating < 0:
            rating_style = "color: #d62728"  # 빨강

        return pd.Series([name_style, rating_style], index=["이름", "누적 승점"])

    # 인덱스는 표시용으로 1부터 시작
    display_df = df.copy()
    display_df.index = range(1, len(display_df) + 1)

    # 스타일 적용
    styled_df = display_df.style\
        .apply(style_row, axis=1)\
        .format({"누적 승점": "{:.1f}"})

    st.dataframe(styled_df, use_container_width=True)


st.markdown('<p style="color: gray; font-size: 14px;">계산 방식: {점수 - 반환점 (+ 1등의 경우 오카)} / 1000 + 우마 보정</p>', unsafe_allow_html=True)
st.markdown('<p style="color: gray; font-size: 12px;">오카 있을시 반환점 30000, 없을시 반환점 25000입니다.  <br>오카란, 각자 반환점에서 일정 수준을 걷은 만큼 초기 점수(25000)를 받을 때, 각자에게 걷은 점수(20000)를 끝나고 모두 1등에게 주는 것입니다.  <br>우마는 N/M 우마시 승점을 3등이 2등에게 N만큼, 4등이 1등에게 M만큼 줍니다.</p>', unsafe_allow_html=True)
st.markdown('<p style="color: gray; font-size: 14px;">2025년 1학기 팀선비 마작대회는 입력 초기 설정대로입니다.  <br>즉, 최종 점수를 1000으로 나눈 이후 1등 +10 / 2등 -20 / 3등 -40 / 4등 -50 이 승점입니다.<br>이 때 25000을 기준으로 보정치는 +35 / +5 / -15 / -25 입니다. 즉 톱 마작이니 1등을 노리는 것이 좋습니다! 작혼과 달리 공격적으로 플레이해 보세요.</p>', unsafe_allow_html=True)


# 게임 기록 출력
if st.session_state.game_history:
    st.subheader("📜 역대 게임 결과")
    for game_idx, game in enumerate(st.session_state.game_history):
        st.write(f"### 게임 {game_idx + 1}")
        df = pd.DataFrame(game)
        df = df.drop(columns=["rank"])
        df.index = range(1, len(df) + 1)
        st.dataframe(df, use_container_width=True)
