import streamlit as st
import pandas as pd

# 세션 상태 초기화
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'game_history' not in st.session_state:
    st.session_state.game_history = []

def calculate_rating(rank, score, okka, uma_n, uma_m):
    base = score / 1000
    
    # 오카 처리
    if okka == "있음":
        score -= 30000
        if rank == 1:
            score += 20000
    elif okka == "없음":
        score -= 25000  # 오카가 없을 경우 모든 플레이어의 점수에서 25,000을 뺌
    
    # 우마 처리
    if rank == 3 and uma_n != 0:
        score += uma_n
    elif rank == 4 and uma_m != 0:
        score += uma_m
    
    # 승점 계산
    if rank == 1:
        return base + 20 + score / 1000
    elif rank == 2:
        return base - 20 + score / 1000
    elif rank == 3:
        return base - 40 + score / 1000
    elif rank == 4:
        return base - 60 + score / 1000
    return base

st.title("🀄 마작 승점 계산기")
st.markdown("4명 게임 기준, 점수와 순위를 기반으로 승점을 자동 계산합니다.")

# 오카 및 우마 설정
okka = st.selectbox("오카 설정", options=["없음", "있음"])
uma_n = st.number_input("3등에게 주는 승점 (N)", min_value=0, max_value=1000, value=10)
uma_m = st.number_input("1등에게 주는 승점 (M)", min_value=0, max_value=1000, value=30)

with st.form("game_form"):
    st.subheader("🎮 새 게임 입력")
    names = []
    scores = []
    for i in range(4):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"{i+1}번 플레이어 이름", key=f"name_{i}")
        with col2:
            score = st.number_input(f"{i+1}번 점수", key=f"score_{i}", step=1000)
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

# 역대 게임 결과 확인
if st.session_state.game_history:
    st.subheader("📜 역대 게임 결과")
    for game_idx, game in enumerate(st.session_state.game_history):
        st.write(f"### 게임 {game_idx + 1}")
        df = pd.DataFrame(game)
        st.dataframe(df, use_container_width=True)

# 누적 승점 출력
if st.session_state.players:
    st.subheader("📊 누적 결과")
    df = pd.DataFrame([
        {"이름": name,
         "누적 점수": data["score"],
         "누적 승점": round(data["rating"], 2)}
        for name, data in st.session_state.players.items()
    ])
    df = df.sort_values(by="누적 승점", ascending=False)
    st.dataframe(df, use_container_width=True)

# 초기화 옵션
if st.button("🔁 모든 기록 초기화"):
    st.session_state.players = {}
    st.session_state.game_history = []
    st.success("데이터가 초기화되었습니다.")
