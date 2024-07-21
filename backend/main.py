import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import yaml
import random
import os
import fnmatch
import glob
import re
import json
import time

app = FastAPI(title="tddd")

CONFIG = {}

TODOS = {}

with open("./config.yaml") as stream:
    try:
        CONFIG = yaml.safe_load(stream)["settings"]
    except yaml.YAMLError as exc:
        print(exc)

comment_indicators = CONFIG["comments"]
todo_indicators = CONFIG["anchors"]
base_dir = CONFIG["root"]
ignore_dir_patterns = CONFIG["dirs"]["ignore"]
include_dir_patterns = CONFIG["dirs"]["include"]

include_file_patterns = CONFIG["files"]["include"]
exclude_file_patterns = CONFIG["files"]["ignore"]

refresh_time = CONFIG["refresh-time"]

previous_time_stamp = 0

comment_pattern = "|".join(re.escape(indicator) for indicator in comment_indicators)
todo_pattern = "|".join(re.escape(indicator) for indicator in todo_indicators)
pattern = re.compile(rf"^\s*({comment_pattern})\s*({todo_pattern})", re.IGNORECASE)
pattern2 = re.compile(rf"^\s*({comment_pattern})", re.IGNORECASE)


def matches_pattern(path, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def find_todos_in_file(file_path):
    todo_comments = []
    with open(file_path, "r") as file:
        reading_item = 0
        content = ""
        line_nb = 0

        for i, line in enumerate(file):
            if reading_item > 0:
                if pattern2.search(line):
                    content += "\n" + line.strip()
                elif reading_item != 1:
                    reading_item -= 1
                    content += "\n" + line.strip()
                else:
                    todo_comments.append({"line": line_nb, "content": content})
                    reading_item = 0
                    content = ""
            else:
                if pattern.search(line):
                    reading_item = 2
                    content = line.strip()
                    line_nb = i

        if reading_item:
            todo_comments.append({"line": line_nb, "content": content})

    return todo_comments


def find_todos():
    result_files = []

    def search_recursive(current_dir):
        if matches_pattern(current_dir, ignore_dir_patterns):
            return

        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            relative_path = os.path.relpath(item_path, base_dir)

            if os.path.isdir(item_path):
                if matches_pattern(relative_path, include_dir_patterns):
                    search_recursive(item_path)
                continue

            file_name = os.path.basename(relative_path)

            if not matches_pattern(file_name, include_file_patterns):
                continue

            if matches_pattern(file_name, exclude_file_patterns):
                continue

            file = os.stat(item_path)

            if file.st_mtime <= previous_time_stamp:
                continue

            result_files.append(item_path)

    # Start the recursive search from the base directory
    search_recursive(base_dir)

    for file_path in result_files:
        print(file_path)
        todos = find_todos_in_file(file_path)
        TODOS[file_path] = todos


find_todos()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global previous_time_stamp
    global TODOS

    await websocket.accept()

    while True:
        print("Updating")

        find_todos()
        previous_time_stamp = time.time()

        # Wait for any message from the client
        # await websocket.receive_text()
        # Send message to the client
        # value = random.randint(0, 10)
        # print("Sending", value)
        # resp = {"value": value}
        await websocket.send_json(TODOS)

        await asyncio.sleep(refresh_time)


app.mount("/", StaticFiles(directory="front", html=True), name="static")
