import importlib
import os

st = importlib.import_module("streamlit")


st.set_page_config(page_title="SKN28 FE", layout="wide")

st.title("SKN28 Frontend")
st.write("이 프런트엔드 앱은 src 바로 아래에 소스가 놓이도록 정리되어 있습니다.")

st.subheader("실행 환경")
st.json(
    {
        "app_env": os.environ.get("APP_ENV", "development"),
        "service_name": os.environ.get("SERVICE_NAME", "fe"),
        "server_address": os.environ.get("STREAMLIT_SERVER_ADDRESS", "0.0.0.0"),
        "server_port": os.environ.get("STREAMLIT_SERVER_PORT", "8501"),
    }
)

st.info("docker compose 또는 uv run --env-file .env 방식으로 같은 환경값을 사용할 수 있습니다.")
