import json
import requests
import shutil
import os
import concurrent.futures
import uuid
import re
from datetime import datetime
from anki.hooks import addHook
from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo

try:
    from .designer import form_qt6 as form
except ImportError:
    from .designer import form_qt5 as form


def download_file(url, folder, file_extension):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        random_string = str(uuid.uuid4())[:8]
        file_name = f"{current_time}_{random_string}.{file_extension}"
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as file:
            shutil.copyfileobj(response.raw, file)
        return file_path
    else:
        return None


def api_lookup(keyword, min_length=12):
    url = f"https://api.immersionkit.com/look_up_dictionary?keyword={keyword}&sort=shortness&min_length={min_length}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            example = data["data"][0]["examples"][0]
            return {
                "sentence": example["sentence"],
                "sentence_with_furigana": example["sentence_with_furigana"],
                "translation": example["translation"],
                "audioURL": f"https://api.immersionkit.com/download_sentence_audio?id={example['id']}",
                "imageURL": f"https://api.immersionkit.com/download_sentence_image?id={example['id']}"
            }
        else:
            return {"error": "No data found for the keyword"}
    else:
        return {"error": "Failed to retrieve data from the API"}


def immersionKit(browser, ids):
    mw = browser.mw

    d = QDialog(browser)
    frm = form.Ui_Dialog()
    frm.setupUi(d)

    config = mw.addonManager.getConfig(__name__)
    selected_source_field = ""
    selected_min_field = 12
    note = mw.col.getNote(ids[0])
    fields = note.keys()

    frm.srcField.addItems(fields)
    fld = config["Source Field"]
    if fld in fields:
        frm.srcField.setCurrentIndex(fields.index(fld))

    frm.minLengthField.setValue(config.get("MinURLLength", 12)) 

    field_values = {}

    for i, sq in enumerate(config["Search Queries"], 1):
        name = sq["Name"]
        fld = sq["Field"]

        lineEdit = QLineEdit(name)
        frm.gridLayout.addWidget(lineEdit, i, 0)

        combobox = QComboBox()
        combobox.setObjectName("targetField")
        combobox.addItem("<ignored>")
        combobox.addItems(fields)
        if fld in fields:
            combobox.setCurrentIndex(fields.index(fld) + 1)
        frm.gridLayout.addWidget(combobox, i, 1)

        field_values[name] = combobox

    frm.gridLayout.setColumnStretch(1, 1)
    frm.gridLayout.setColumnMinimumWidth(1, 120)

    columns = ["Name", "Target Field"]
    for i, title in enumerate(columns):
        frm.gridLayout.addWidget(QLabel(title), 0, i)

    if d.exec():
        meta_data = {
            "Source Field": frm.srcField.currentText(),
            "Delimiter": config["Delimiter"],
            "Search Queries": [{"Name": name, "Field": combobox.currentText()} for name, combobox in field_values.items()],
            "MinURLLength": frm.minLengthField.value()
        }
        mw.addonManager.writeConfig(__name__, meta_data)

        selected_source_field = frm.srcField.currentText()
        selected_min_field = frm.minLengthField.value()
    else:
        return


    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for nid in ids:
            futures.append(executor.submit(process_note, nid, field_values, selected_source_field, selected_min_field))

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred: {e}")
    mw.reset()
    showInfo("Done Updating!")


def process_note(nid, field_values, selected_source_field, selected_min_field):
    note = mw.col.getNote(nid)
    keyword = note[selected_source_field]
    api_response = api_lookup(keyword, selected_min_field)
    if "error" not in api_response:
        sentence = fix_sentence(api_response["sentence"], keyword, False)
        sentence_with_furigana = fix_sentence(api_response["sentence_with_furigana"], keyword, True)
        translation = api_response["translation"]
        audio_url = api_response["audioURL"]
        image_url = api_response["imageURL"]

        audio_path = download_file(audio_url, mw.col.media.dir(), "mp3")
        if audio_path and field_values["Audio"].currentText() != "<ignored>":
            note[field_values["Audio"].currentText()] = f'[sound:{os.path.basename(audio_path)}]'

        image_path = download_file(image_url, mw.col.media.dir(), "png")
        if image_path and field_values["Image"].currentText() != "<ignored>":
            note[field_values["Image"].currentText()] = f'<img src="{os.path.basename(image_path)}">'

        if field_values["Sentence"].currentText() != "<ignored>":
            note[field_values["Sentence"].currentText()] = sentence
        if field_values["Sentence With Furigana"].currentText() != "<ignored>":
            note[field_values["Sentence With Furigana"].currentText()] = sentence_with_furigana
        if field_values["English Translation"].currentText() != "<ignored>":
            note[field_values["English Translation"].currentText()] = translation
        note.flush()


def fix_sentence(sentence, keyword, setting):
    sentence = re.sub(r'[　→]', '', sentence)
    keyword_pattern = re.escape(keyword)
    keyword_with_reading_pattern = rf'{keyword_pattern}\[(.*?)\]'
    if setting:
        sentence = re.sub(keyword_with_reading_pattern, r'<b>\g<0></b>', sentence)
    else:
        sentence = re.sub(keyword_pattern, f'<b>{keyword}</b>', sentence)
    return sentence



def onAddFields(browser):
    nids = browser.selectedNotes()
    if not nids:
        return
    immersionKit(browser, nids)


def setupMenu(browser):
    menu = browser.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Add Immersion Kit')
    a.triggered.connect(lambda _, b=browser: onAddFields(b))


addHook("browser.setupMenus", setupMenu)
