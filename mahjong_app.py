import streamlit as st
import pandas as pd

# 세션 상태 초기화
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'game_history' not in st.session_state:
    st.session_state.game_history = []

def calculate_rating(rank, score, okka, uma_n, uma_m):
    # 오카 보정 처리
    if okka == "있음":
        first_bonus = 20000
        returning_score = 30000
    elif okka == "없음":
        first_bonus = 0
        returning_score = 25000

    # 기본 승점 계산 (오카 보정이 끝난 후 계산)
    if rank == 1:
        rating = (score + first_bonus - returning_score) / 1000 + uma_m
    elif rank == 2:
        rating = (score - returning_score) / 1000 + uma_n
    elif rank == 3:
        rating = (score - returning_score) / 1000 - uma_n
    elif rank == 4:
        rating = (score - returning_score) / 1000 - uma_m
    else:
        rating = score / 1000
    
    return rating

st.title("🀄 마작 승점 계산기")
st.markdown("4명 게임 기준, 점수와 순위를 기반으로 승점을 자동 계산합니다.")

# 새 게임 입력을 위한 UI
with st.form("game_form"):
    st.subheader("🎮 새 게임 입력")
    
    # 오카 및 우마 설정
    okka = st.selectbox("오카 설정", options=["있음", "없음"], index=0)  # 기본값을 "있음"으로 설정
    uma_n = st.number_input("3등에게 주는 승점 (N)", value=10)  # 우마 N에 대한 제한 제거
    uma_m = st.number_input("1등에게 주는 승점 (M)", value=30)  # 우마 M에 대한 제한 제거

    # 플레이어 점수 입력 (4등까지 입력)
    names = []
    scores = []
    for i in range(4):  # 4명의 플레이어 점수 입력
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"{i+1}등 플레이어 이름", key=f"name_{i}")
        with col2:
            score = st.number_input(f"{i+1}등 점수", key=f"score_{i}", step=100)
        names.append(name)
        scores.append(score)

    submitted = st.form_submit_button("게임 결과 저장")

if submitted:
    # 데이터 정리 및 정렬
    game_data = sorted(zip(names, scores), key=lambda x: x[1], reverse=True)

    game_result = []
    for rank, (name, score) in enumerate(game_data, 1):
        rating = calculate_rating(rank, score, okka, uma_n, uma_m)
        if name not in st.session_state.players:
            st.session_state.players[name] = {'score': 0, 'rating': 0}
        st.session_state.players[name]['score'] += score
        st.session_state.players[name]['rating'] += rating
        
        game_result.append({
            'name': name,
            'score': score,
            'rank': rank,
            'rating': round(rating, 2)
        })

    st.session_state.game_history.append(game_result)

    st.success("✅ 게임 결과가 저장되었습니다.")

# 누적 승점 출력
if st.session_state.players:
    st.subheader("📊 누적 승점 결과")
    df = pd.DataFrame([
        {"이름": name, "누적 승점": round(data["rating"], 2)}
        for name, data in st.session_state.players.items()
    ])
    df = df.sort_values(by="누적 승점", ascending=False)
    st.dataframe(df, use_container_width=True)

# 역대 게임 결과 확인
if st.session_state.game_history:
    st.subheader("📜 역대 게임 결과")
    for game_idx, game in enumerate(st.session_state.game_history):
        st.write(f"### 게임 {game_idx + 1}")
        df = pd.DataFrame(game)
        st.dataframe(df, use_container_width=True)

# 초기화 옵션
if st.button("🔁 모든 기록 초기화"):
    st.session_state.players = {}
    st.session_state.game_history = []
    st.success("데이터가 초기화되었습니다.")
