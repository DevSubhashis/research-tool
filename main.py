import streamlit as st
from rag import procress_url, generate_answer

st.title("Research Tool")

url = st.sidebar.text_input("URL");

placeholder = st.empty()

process_url_button = st.sidebar.button("Process URL")

if process_url_button:
    if url == '' :
        placeholder.text("You Must Provide URL")
    else: 
        for status in procress_url([url]):
            placeholder.text(status)


query = placeholder.text_input("Enter your Question")
if query:
    try: 
        answer, sources = generate_answer(query)
        st.header("Answer: ")
        st.write(answer)

        if sources:
            st.subheader("Sources: ")
            for source in sources.split("\n"):
                st.write(source)
    except RuntimeError as e:
        placeholder.text("You must process url first")
