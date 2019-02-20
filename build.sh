#!/usr/bin/env bash

pipreqs . --encoding=utf-8 --force
pip3 install -r requirements.txt
pyinstaller ./mainView.spec --onefile