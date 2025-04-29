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
    for i, player in enumerate(game_result):
        player_name = player['name']
        player_score = player['score']
        player_rank = player['rank']
        player_rating = player['rating']
        
        # 각 플레이어 정보를 새로운 행으로 기록
        sheet.append_row([game_id, str(game_result), player_name, player_score, player_rank, player_rating, timestamp])

# 새로고침 및 세션을 새로 시작할 때마다 시트에서 데이터를 불러오는 로직
def reload_game_history():
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

# 처음 로드 시 시트에서 데이터를 불러오기
if 'game_history' not in st.session_state:
    reload_game_history()

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
st.title("🀄 마작 승점 계산기")
st.markdown("4명 게임 기준, 점수와 순위를 기반으로 승점을 자동 계산합니다.")

# 새 게임 입력
with st.form("game_form"):
    st.subheader("🎮 새 게임 입력")

    okka = st.selectbox("오카 설정", options=["있음", "없음"], index=0)
    uma_n = st.number_input("3등에게 주는 승점 (N)", value=10)
    uma_m = st.number_input("1등에게 주는 승점 (M)", value=30)

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

if submitted:
    game_data = sorted(zip(names, scores), key=lambda x: x[1], reverse=True)

    game_result = []
    for rank, (name, score) in enumerate(game_data, 1):
        rating = calculate_rating(rank, score, okka, uma_n, uma_m)
        if name not in st.session_state.players:
            st.session_state.players[name] = {'score': 0, 'rating': 0}
        st.session_state.players[name]['score'] += score
        st.session_state.players[name]['rating'] += rating
        game_result.append({'name': name, 'score': score, 'rank': rank, 'rating': round(rating, 2)})

    # 게임 결과를 시트에 저장
    save_game_to_sheet(game_result, len(st.session_state.game_history) + 1)

    # 게임 기록 업데이트 후 새로 고침
    reload_game_history()  # 세션에 업데이트된 데이터를 새로 로드

    st.success("✅ 게임 결과가 저장되었습니다.")

# 누적 승점 출력
if st.session_state.players:
    st.subheader("📊 누적 승점 결과")
    df = pd.DataFrame([{
        "이름": name,
        "누적 승점": round(data["rating"], 2)
    } for name, data in st.session_state.players.items()])
    df = df.sort_values(by="누적 승점", ascending=False).reset_index(drop=True)
    df["순위"] = df.index + 1
    st.dataframe(df[['순위', '이름', '누적 승점']], use_container_width=True)

# 게임 기록 출력
if st.session_state.game_history:
    st.subheader("📜 역대 게임 결과")
    for game_idx, game in enumerate(st.session_state.game_history):
        st.write(f"### 게임 {game_idx + 1}")
        df = pd.DataFrame(game)
        st.dataframe(df, use_container_width=True)

# 초기화 기능 (시트는 초기화 안 함)
if st.button("🔁 세션 초기화"):
    reload_game_history()  # 구글 시트에서 데이터를 다시 불러옴
    st.success("세션 데이터가 초기화되었습니다. (Google Sheets 데이터는 유지됩니다)")
