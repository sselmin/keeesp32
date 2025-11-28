#!/usr/bin/env python3
import os

folders = ["picoweb","utemplate"]

for folder in folders:
    try:
        if folder not in os.listdir():
            os.mkdir(folder)
            print(f"Created folder: {folder}")
        else:
            print(f"Folder already exists: {folder}")
    except Exception as e:
        print(f"Error creating folder {folder}: {e}")
