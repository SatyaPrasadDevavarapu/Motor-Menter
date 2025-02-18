import streamlit as st
import base64
import time
import shutil
import os

from file_chat_input import file_chat_input
from streamlit_float import float_init

from constants import USER_ID, SESSION_ID, pdf_mapping
from databases.MongoDB.utils import insert_data, get_full_data, get_file_details
from image_processing.image_summary import get_image_summary_roboflow
from services import get_response, generalize_image_summary
from utils import pdf_to_images

float_init()


def page_switcher(page):
    st.session_state.runpage = page


def main():
    st.title("BOSCH Hackathon Chatbot")
    container = st.container()
    with container:
        user_input = file_chat_input("What is up?")

    # prev_records = check_and_delete_existing_records(USER_ID, SESSION_ID)
    # print(prev_records)
    full_data = get_full_data(USER_ID, SESSION_ID)
    full_data.reverse()

    for message in full_data:
        with st.chat_message("user"):
            st.markdown(message["query"])
        with st.chat_message("assistant"):
            st.markdown(message["response"])

    if "user_input_processed" not in st.session_state:
        st.session_state.user_input_processed = False
    if "current_input" not in st.session_state:
        st.session_state.current_input = None

    if user_input:
        is_image = False
        if st.session_state.current_input != user_input:
            st.session_state.user_input_processed = False
            st.session_state.current_input = user_input

        if not st.session_state.user_input_processed:
            response, image_id, pdf_pages, df, table_response = (
                None,
                None,
                None,
                None,
                None,
            )

            if user_input["message"] != "":
                start_time = time.time()
                if len(user_input["files"]) == 0:
                    print(
                        "\n--------------------Question with Text--------------------\n"
                    )
                    response, image_id, pdf_pages, df, table_response, flag_probe = get_response(
                        user_input["message"]
                    )

                elif len(user_input["files"]) != 0:
                    is_image = True
                    print(
                        "\n--------------------Question with both Text and Image--------------------\n"
                    )
                    base64_string = user_input["files"][0]["content"]
                    image_format = None
                    if base64_string.startswith("data:image/png;base64,"):
                        base64_string = base64_string.replace(
                            "data:image/png;base64,", ""
                        )
                        image_format = "png"
                    elif base64_string.startswith("data:image/jpeg;base64,"):
                        base64_string = base64_string.replace(
                            "data:image/jpeg;base64,", ""
                        )
                        image_format = "jpeg"
                    elif base64_string.startswith("data:image/jpg;base64,"):
                        base64_string = base64_string.replace(
                            "data:image/jpg;base64,", ""
                        )
                        image_format = "jpg"

                    image_data = base64.b64decode(base64_string)
                    input_image_directory_path = "input_data/user_image_input"
                    if not os.path.exists(input_image_directory_path):
                        os.makedirs(input_image_directory_path, exist_ok=True)
                    image_path = (
                        f"input_data/user_image_input/input_image.{image_format}"
                    )
                    with open(image_path, "wb") as f:
                        f.write(image_data)
                    image_summary = get_image_summary_roboflow(image_path)
                    query = f"""{image_summary} - This is a summary of an image uploaded by the user, 
                    with this data answer the following question {user_input['message']}"""

                    response, image_id, pdf_pages, df, table_response, flag_probe = get_response(
                        query
                    )

                    with st.chat_message("user"):
                        st.image(
                            image_data, caption="Uploaded Image", use_column_width=True
                        )

                    if os.path.exists(input_image_directory_path) and os.path.isdir(
                        input_image_directory_path
                    ):
                        shutil.rmtree(input_image_directory_path)

                end_time = time.time()
                execution_time = end_time - start_time
                print(f"\n\n\nExecution time: {execution_time} seconds")

                print(image_id)

                print(f"flag_probe = {flag_probe}")

                insert_data(USER_ID, SESSION_ID, user_input["message"], response, flag_probe)

                with st.chat_message("user"):
                    st.write(f"{user_input['message']}")

                with st.chat_message("assistant"):
                    st.write(f"{response}")

                if df is not None:
                    st.dataframe(df)
                    st.write("Related Table")
                    st.write(f"{table_response}")

                if df is None and table_response is not None:
                    st.write(f"{table_response}")
                    st.write("Related JSON Data")

                # print(is_image)
                if image_id and not is_image:
                    try:
                        img_bytes = base64.b64decode(
                            get_file_details(image_id)["encoded_val"]
                        )
                        # if img_bytes:
                        #     print("img bytesTrue")
                        # else:
                        #     print("no bytes False")
                        st.image(
                            img_bytes, caption="Related Image", use_column_width=True
                        )
                    except Exception as e:
                        st.error(f"Failed to display image: {e}")

                if pdf_pages:
                    st.session_state.pdf_pages = pdf_pages
                    st.session_state.show_pdf_btn = True

                st.session_state.user_input_processed = True

            if user_input["message"] == "" and len(user_input["files"]) != 0:
                is_image = True
                print("\n--------------------Question with Image--------------------\n")
                base64_string = user_input["files"][0]["content"]
                image_format = None
                if base64_string.startswith("data:image/png;base64,"):
                    base64_string = base64_string.replace("data:image/png;base64,", "")
                    image_format = "png"
                elif base64_string.startswith("data:image/jpeg;base64,"):
                    base64_string = base64_string.replace("data:image/jpeg;base64,", "")
                    image_format = "jpeg"
                elif base64_string.startswith("data:image/jpg;base64,"):
                    base64_string = base64_string.replace("data:image/jpg;base64,", "")
                    image_format = "jpg"

                image_data = base64.b64decode(base64_string)
                input_image_directory_path = "input_data/user_image_input"
                if not os.path.exists(input_image_directory_path):
                    os.makedirs(input_image_directory_path, exist_ok=True)
                image_path = f"input_data/user_image_input/input_image.{image_format}"
                with open(image_path, "wb") as f:
                    f.write(image_data)
                image_summary = generalize_image_summary(get_image_summary_roboflow(image_path))

                with st.chat_message("user"):
                    st.image(
                        image_data, caption="Uploaded Image", use_column_width=True
                    )
                with st.chat_message("assistant"):
                    st.write(image_summary)

                if os.path.exists(input_image_directory_path) and os.path.isdir(
                    input_image_directory_path
                ):
                    shutil.rmtree(input_image_directory_path)

                st.session_state.user_input_processed = True

    if st.session_state.get("show_pdf_btn", False):
        if st.button("View Reference PDF Contents"):
            st.session_state.runpage = reference_pdf
            st.rerun()

    container.float("bottom: 0")


def reference_pdf():
    st.title("Reference PDF")
    pdf_pages = st.session_state.pdf_pages
    if st.button("Go back to Chat"):
        st.session_state.runpage = main
        st.rerun()

    carousel_indicators = ""
    carousel_items = ""
    page_num = 0

    for car_name in pdf_pages.keys():
        image_paths = pdf_to_images(
            f"./input_data/{pdf_mapping[car_name]}", list(set(pdf_pages[car_name]))
        )
        for i, img_str in enumerate(image_paths):
            active_class = "active" if page_num == 0 else ""
            carousel_indicators += f'<li data-target="#myCarousel" data-slide-to="{page_num}" class="{active_class}"></li>'
            carousel_items += f"""
            <div class="item {active_class}">
                <img src="data:image/png;base64,{img_str}" alt="Page {page_num+1}" style="width:100%;">
            </div>
            """
            page_num += 1

    path_to_html = "./display_carousel.html"
    with open(path_to_html, "r") as f:
        html_data = f.read()

    html_data = html_data.replace("{{carousel_indicators}}", carousel_indicators)
    html_data = html_data.replace("{{carousel_items}}", carousel_items)

    st.components.v1.html(html_data, height=1000)


if __name__ == "__main__":
    if "runpage" not in st.session_state:
        st.session_state.runpage = main
    st.session_state.runpage()
