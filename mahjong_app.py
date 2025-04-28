import streamlit as st
import pandas as pd

# 세션 상태 초기화
if 'players' not in st.session_state:
    st.session_state.players = {}

def calculate_rating(rank, score):
    base = score / 1000
    if rank == 1:
        return base + 20
    elif rank == 2:
        return base - 20
    elif rank == 3:
        return base - 40
    elif rank == 4:
        return base - 60

st.title("🀄 마작 승점 계산기")
st.markdown("4명 게임 기준, 점수와 순위를 기반으로 승점을 자동 계산합니다.")

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

    for rank, (name, score) in enumerate(game_data, 1):
        rating = calculate_rating(rank, score)
        if name not in st.session_state.players:
            st.session_state.players[name] = {'score': 0, 'rating': 0}
        st.session_state.players[name]['score'] += score
        st.session_state.players[name]['rating'] += rating

    st.success("✅ 게임 결과가 저장되었습니다.")

# 결과 출력
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
    st.success("데이터가 초기화되었습니다.")
