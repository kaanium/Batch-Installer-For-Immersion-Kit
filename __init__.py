import json
import requests
import shutil
import os
import concurrent.futures
import uuid
import re
import random
from datetime import datetime
from anki.hooks import addHook
from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo

try:
    from .designer import form_qt6 as form
except ImportError:
    from .designer import form_qt5 as form

class SelectedSettings:
    def __init__(self, source_field, min_length, exact, highlighting, tag, merge):
        self.source_field = source_field
        self.min_length = min_length
        self.exact = exact
        self.highlighting = highlighting
        self.tag = tag
        self.merge = merge


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

def get_context(_id):
    url = f"https://api.immersionkit.com/sentence_with_context?id={_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "prev": data["pretext_sentences"][-1]["sentence"],
            "next": data["posttext_sentences"][0]["sentence"],
            "prev_furigana": data["pretext_sentences"][-1]["sentence_with_furigana"],
            "next_furigana": data["posttext_sentences"][0]["sentence_with_furigana"]
            }
    

def api_lookup(keyword, min_length=12, selected_exact=False, is_random=False):
    if selected_exact:
        url = f"https://api.immersionkit.com/look_up_dictionary?keyword=「{keyword}」&sort=shortness&min_length={min_length}"
    else:
        url = f"https://api.immersionkit.com/look_up_dictionary?keyword={keyword}&sort=shortness&min_length={min_length}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            if not is_random:
                example = data["data"][0]["examples"][0]
            else:
                try:
                    example = random.choice(data["data"][0]["examples"])
                except:
                    return {"error": "No sentences is found for this settings"}
            _id = example["id"]
            context = get_context(_id)
            return {
                "sentence": example["sentence"],
                "sentence_with_furigana": example["sentence_with_furigana"],
                "translation": example["translation"],
                "deck_name": example["deck_name"],
                "audioURL": f"https://api.immersionkit.com/download_sentence_audio?id={example['id']}",
                "imageURL": f"https://api.immersionkit.com/download_sentence_image?id={example['id']}",
                "prev_text": context["prev"],
                "next_text": context["next"],
                "prev_text_furigana": context["prev_furigana"],
                "next_text_furigana": context["next_furigana"]
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
    note = mw.col.getNote(ids[0])
    fields = note.keys()

    frm.srcField.addItems(fields)
    fld = config["Source Field"]
    if fld in fields:
        frm.srcField.setCurrentIndex(fields.index(fld))

    frm.minLengthField.setValue(config.get("MinURLLength", 12)) 

    field_values = {}

    frm.exactSearchCheckBox.setChecked(config.get("ExactSearch", False))
    frm.highlightingCheckBox.setChecked(config.get("Highlighting", False))
    frm.sourceMediaTagCheckBox.setChecked(config.get("Tag", False))
    frm.mergeCheckbox.setChecked(config.get("Merge", False))

    
    addon_folder = os.path.dirname(__file__)
    fields_path = os.path.join(addon_folder, 'fields.json')

    with open(fields_path, 'r') as file:
        fields_data = json.load(file)

    comboboxes = []
    append_checkboxes = []
    _append_checkboxes = {}

    for i in range(len(fields_data["Search Queries"])):
        name = fields_data["Search Queries"][i]["Name"]
        try:
            fld = config["Search Queries"][i]["Field"]
            append_checked = config["Search Queries"][i].get("Append", False)
        except:
            fld = ""
            append_checked = False

        lineEdit = QLineEdit(name)
        frm.gridLayout.addWidget(lineEdit, i+1, 0)

        combobox = QComboBox()
        combobox.setObjectName("targetField")
        combobox.addItem("<ignored>")
        combobox.addItems(fields)
        if fld in fields:
            combobox.setCurrentIndex(fields.index(fld) + 1)
        frm.gridLayout.addWidget(combobox, i+1, 1)
        comboboxes.append(combobox)

        append_checkbox = QCheckBox()
        append_checkbox.setChecked(append_checked)
        frm.gridLayout.addWidget(append_checkbox, i+1, 2)
        append_checkboxes.append(append_checkbox)

        field_values[name] = combobox

    frm.gridLayout.setColumnStretch(1, 1)
    frm.gridLayout.setColumnMinimumWidth(1, 120)

    columns = ["Name", "Target Field", "Append"]
    for i, title in enumerate(columns):
        frm.gridLayout.addWidget(QLabel(title), 0, i)

    if d.exec():
        meta_data = {
            "Source Field": frm.srcField.currentText(),
            "Delimiter": config["Delimiter"],
            "Search Queries": [{"Name": name, "Field": combobox.currentText(), "Append": append.isChecked()}
                               for name, combobox, append in zip(field_values.keys(), comboboxes, append_checkboxes)],
            "MinURLLength": frm.minLengthField.value(),
            "ExactSearch": frm.exactSearchCheckBox.isChecked(), 
            "Highlighting": frm.highlightingCheckBox.isChecked(),
            "Tag": frm.sourceMediaTagCheckBox.isChecked(),
            "Merge": frm.mergeCheckbox.isChecked()
        }

        mw.addonManager.writeConfig(__name__, meta_data)

        selected = SelectedSettings(
            frm.srcField.currentText(),
            frm.minLengthField.value(),
            frm.exactSearchCheckBox.isChecked(),
            frm.highlightingCheckBox.isChecked(),
            frm.sourceMediaTagCheckBox.isChecked(),
            frm.mergeCheckbox.isChecked()
        )
        _append_checkboxes = {name: append.isChecked() for name, append in zip(field_values.keys(), append_checkboxes)}
    else:
        return


    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        progress = QProgressDialog('Importing from Immersion Kit', 'Cancel', 0, len(ids))
        bar = QProgressBar(progress)
        bar.setFormat('%v/%m')
        bar.setMaximum(len(ids))
        progress.setBar(bar)
        progress.setMinimumDuration(1000)
        progress.setModal(True)
        counter = 0
        for nid in ids:
            futures.append(executor.submit(process_note, nid, field_values, selected, _append_checkboxes))

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
                counter += 1
                progress.setValue(counter)
            except Exception as e:
                print(f"An error occurred: {e}")
                counter += 1
                progress.setValue(counter)
            if progress.wasCanceled():
                break
    mw.reset()
    QMessageBox.information(None, "Done", "Done Updating!")

def update_field(note, field, value, trigger_mode, append=False):
    if trigger_mode:
        field = field.currentText()
    if field != "<ignored>":
        if append:
            note[field] += " " + value
        else:
            note[field] = value


def update_note(note, field_values, api_response, selected, mode, keyword, append_checkboxes):
    if "error" not in api_response:
        sentence = fix_sentence(api_response["sentence"], keyword, False, selected.highlighting)
        sentence_with_furigana = fix_sentence(api_response["sentence_with_furigana"], keyword, True, selected.highlighting)
        translation = api_response["translation"]
        audio_url = api_response["audioURL"]
        image_url = api_response["imageURL"]
        source = api_response["deck_name"]
        _prev = api_response["prev_text"]
        _next = api_response["next_text"]
        _prev_furigana = api_response["prev_text_furigana"]
        _next_furigana = api_response["next_text_furigana"]

        audio_path = download_file(audio_url, mw.col.media.dir(), "mp3")
        if audio_path:
            update_field(note, field_values["Audio"], f'[sound:{os.path.basename(audio_path)}]', mode, append_checkboxes["Audio"])

        image_path = download_file(image_url, mw.col.media.dir(), "png")
        if image_path:
            update_field(note, field_values["Image"], f'<img src="{os.path.basename(image_path)}">', mode, append_checkboxes["Image"])

        if not selected.merge:
            update_field(note, field_values["Sentence"], sentence, mode, append_checkboxes["Sentence"])
            update_field(note, field_values["Sentence With Furigana"], sentence_with_furigana, mode,append_checkboxes["Sentence With Furigana"])
        else:
            update_field(note, field_values["Sentence"], "<small>" + _prev + "</small><br><big> " + sentence + " </big><br><small>" + _next + "</small>", mode, append_checkboxes["Sentence"])
            update_field(note, field_values["Sentence With Furigana"], "<small>" + _prev_furigana + "</small><br><big> " + sentence_with_furigana + " </big><br><small>" + _next_furigana + "</small>", mode, append_checkboxes["Sentence With Furigana"])
        update_field(note, field_values["English Translation"], translation, mode, append_checkboxes["English Translation"])
        update_field(note, field_values["Source Media"], source, mode, append_checkboxes["Source Media"])
        update_field(note, field_values["Previous Sentence"], _prev, mode, append_checkboxes["Previous Sentence"])
        update_field(note, field_values["Next Sentence"], _next, mode, append_checkboxes["Next Sentence"])
        if selected.tag:
            tag = source.replace(" ", "::")
            note.addTag(tag)


def process_note(nid, field_values, selected, append_checkboxes):
    note = mw.col.getNote(nid)
    keyword = note[selected.source_field]
    api_response = api_lookup(keyword, selected.min_length, selected.exact)
    update_note(note, field_values, api_response, selected, True, keyword, append_checkboxes)
    note.flush()

def on_reroll_immersion_kit_key_press(_browser):
    if _browser is None:
        card = mw.reviewer.card
        note_id = card.nid
    else:
        note_id = _browser.selectedNotes()[0]

    note = mw.col.getNote(note_id)

    
    config = mw.addonManager.getConfig(__name__)
    selected = SelectedSettings(
        config.get("Source Field", "Front"),
        config.get("MinURLLength", 12),
        config.get("ExactSearch", False),
        config.get("Highlighting", False),
        config.get("Tag", False),
        config.get("Merge", False)
    )
    keyword = note[selected.source_field]

    field_values = {}

    addon_folder = os.path.dirname(__file__)
    fields_path = os.path.join(addon_folder, 'fields.json')

    with open(fields_path, 'r') as file:
        fields_data = json.load(file)

    append_checkboxes = {}

    for i in range(len(fields_data["Search Queries"])):
        name = fields_data["Search Queries"][i]["Name"]
        try:
            fld = config["Search Queries"][i]["Field"]
            append_checked = config["Search Queries"][i].get("Append", False)
        except:
            fld = ""
            append_checked = False

        field_values[name] = fld
        append_checkboxes[name] = append_checked

    api_response = api_lookup(keyword, selected.min_length, selected.exact, True)
    
    update_note(note, field_values, api_response, selected, False, keyword, append_checkboxes)

    mw.col.update_note(note)

    if _browser is None:
        mw.reviewer._redraw_current_card()
    else:
        mw.reset()


def fix_sentence(sentence, keyword, setting, selected_highlighting):
    sentence = re.sub(r'[　→]', '', sentence)
    if selected_highlighting:
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

    reroll_immersion_kit_action = QAction('Get new example sentence', browser)
    reroll_immersion_kit_shortcut = QKeySequence("Shift+K")
    reroll_immersion_kit_action.setShortcut(reroll_immersion_kit_shortcut)
    reroll_immersion_kit_action.triggered.connect(lambda _, b=browser: on_reroll_immersion_kit_key_press(b))
    menu.addAction(reroll_immersion_kit_action)
    menu.addSeparator()
    a = menu.addAction('Add Immersion Kit')
    a.triggered.connect(lambda _, b=browser: onAddFields(b))
    


addHook("browser.setupMenus", setupMenu)

reroll_immersion_kit_action = QAction('Get new example sentence', mw)
reroll_immersion_kit_shortcut = QKeySequence("Ctrl+K")
reroll_immersion_kit_action.setShortcut(reroll_immersion_kit_shortcut)
reroll_immersion_kit_action.triggered.connect(lambda: on_reroll_immersion_kit_key_press(None))
mw.form.menuTools.addAction(reroll_immersion_kit_action)

