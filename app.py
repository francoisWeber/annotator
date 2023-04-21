import argparse
import streamlit as st
import json
import os
from os import path as osp
import sys
from fit_etl.extract import Workout

st.title("Give your run a label !")


def parse_args(args):
    parser = argparse.ArgumentParser("Data Diagnostics")
    parser.add_argument("youpi", help="CSV file")
    return parser.parse_args(args)


args = parse_args(sys.argv[1:])

INPUT_DIR = "./data/raw"
QUESTIONS_PATH = "./questions.json"
OUTPUT_PATH = "./answered-questions.json"


with open(osp.join(QUESTIONS_PATH)) as f:
    questions = json.load(f)
ALLOWED_EXT_LOWER = ["fit"]


def question_info2streamlit(question: dict):
    if question["type"] == "number":
        el = st.slider(
            question["label"],
            min_value=question["bounds"][0],
            max_value=question["bounds"][1],
            value=question["default"],
            step=1,
            disabled=False,
            label_visibility="visible",
        )
        return el
    elif question["type"] == "bool":
        el = st.checkbox(question["label"], value=True)
    elif question["type"] == "enum":
        el = st.selectbox(question["label"], question["enum"], on_change=get_next_item)
    return el


def gather(questions, st_questions):
    return {question["id"]: answer for question, answer in zip(questions, st_questions)}


def list_files(directory, previous_data=None):
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if any([f.lower().endswith(ext) for ext in ALLOWED_EXT_LOWER])
    ]
    if previous_data:
        already_marked_files = list(previous_data.keys())
        files = [i for i in files if i not in already_marked_files]
    return files


def maybe_load_previous_data(path) -> dict:
    if osp.isfile(path):
        with open(path) as f:
            return json.load(f)
    else:
        return {}


if "previous_data" not in st.session_state:
    previous_data = maybe_load_previous_data(OUTPUT_PATH)
    st.session_state.previous_data = previous_data

if "files_paths" not in st.session_state:
    files_paths = list_files(INPUT_DIR, st.session_state.previous_data)
    st.session_state.files_paths = files_paths

if "idx" not in st.session_state:
    st.session_state.idx = len(st.session_state.previous_data)

if "max_id" not in st.session_state:
    st.session_state.max_id = len(st.session_state.files_paths)

if "data_infos" not in st.session_state:
    st.session_state.data_infos = st.session_state.previous_data


def save():
    with open(osp.join(OUTPUT_PATH), "w") as f:
        json.dump(st.session_state.data_infos, f, indent=2)


def get_next_item():
    if st.session_state.idx < st.session_state.max_id - 1:
        st.session_state.idx += 1
    else:
        st.write("This was the last")
        save()
        st.stop()


bar_context, figure_context = st.columns([2, 1])
with bar_context:
    st.progress(st.session_state.idx / st.session_state.max_id)
with figure_context:
    st.text(f"{st.session_state.idx}e element en cours sur {st.session_state.max_id}")
    # st.metric(label="en cours", value=st.session_state.idx)
    # st.metric(label="total", value=st.session_state.max_id)
image_context, form_context = st.columns([3, 1])

with st.form("form", clear_on_submit=True):
    file = st.session_state.files_paths[st.session_state.idx]
    if file in st.session_state.data_infos:
        get_next_item()
    with image_context:
        st.text(osp.basename(file))
        workout = Workout.from_fit(file)
        st.pyplot(workout.plot_basics())
    with form_context:
        st_questions = [question_info2streamlit(question) for question in questions]
    submitted = st.form_submit_button("go", on_click=get_next_item)
    if submitted:
        infos = gather(questions, st_questions)
        st.session_state.data_infos[file] = infos
save_btn = st.button("save", on_click=save)
