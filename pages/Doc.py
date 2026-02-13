import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Docs - LangGraph AI Agent", page_icon="🤖", layout="centered"
)
st.title(":red[Docs --]", anchor=False)
st.divider()


st.markdown(
    """
# 🌐 LangGraph Web Search Agent

A stateful AI Agent built with **LangGraph**, **Streamlit**, and **Google Gemini 2.0 Flash**. This agent is capable of browsing the web using DuckDuckGo to provide real-time, researched answers to user queries.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agent-orange)
![Gemini](https://img.shields.io/badge/Google_Gemini-2.0_Flash-magenta)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)

## 🧠 Architecture

The agent operates on a cyclic graph architecture. It can loop between "Thinking" (LLM) and "Acting" (Web Search) until it arrives at a satisfactory answer.
"""
)
iframe_src = "https://mermaid.live/view#pako:eNplVH9v2jAQ_SonS1WDBmkpUGhUMXWEokn8mEKmqVumKiTXkC2xkeOoMMR338VuoKj-y3bu3Xv37pw9i0SMzGGJDDdr8N2AA62LC5jTfWFOS__B8y1rqUKpGg1otYYwX7jj54fJeO4H3AQV5crkCNg05MlE738I-fclE68BM0HVOkF_Bex-NXxIkCtNd3-1Gt6v5NWwbcNX_gcjBctdoTCHb1LkGwWfYFRKWYW7oUIdemPDKMwymE5nYE0wT3kKN_Y1PGZhsW7okI4NE-QoCQIeFhvBC4SFB74QmQYH7LfjOJwULNUuw7qianmL7_7Y22uhnigVyqNIq1iLMoufI8FVyks0ZG4aay1RJSoERRyfA3ag_DFGaZEK_oFDG-IvFtOlMUTrOvNjvMWIuOGx5JGiFA684uq5wFBGa6Nlmq5kKHcOxHFSNExBFfcbWUWDPK5Zx3PXssY8bjTqG2r4OE6wgCtyjvrFzzule268qBHmRB-o4U8EtI52wqMoKXfATpOiq_uImwuC4VYd21KDSGDNc8IbjIeqlByWuvgKWGaqeM91NpVU14j6U3HMhXpzgtOubbw-ny8zdGTw0fkv-CIk6m6mPKk62yTvIdWBjg65fD-TDjzRas1mLde91J-VgERWhoBaI-TU1ozgoNIcberTO0XQss9qYE16lWnMHCVLbLIcZR5WR7avQAGjfDkGzKFtjC8h-VA9swPBNiH_KUReI4k-WdeHchOTTjcN6bWeImg4UI5IpmJOTydgzp5tmdPu3trddrt71x50u_1Or9NkO7od2L3bm-7ddafX6wz6t_1Dk_3TjNf2oE8JME6VkDPzb9G_mMN_LOxc4A"
st.subheader("***Flowchart:***")
components.iframe(iframe_src, width=900, height=750)
