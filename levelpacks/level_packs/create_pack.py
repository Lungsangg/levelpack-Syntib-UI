import yaml
import base64
import streamlit as st
import os

from pathlib import Path
from .corpus_segment import Tokenizer
from .google_drive import upload_to_drive, download_drive
from .generate_to_tag import generate_to_tag
from .convert2plaintxt import convert2plaintxt
from .extract_level_content import extract_content
from .onto_from_tagged import onto_from_tagged
from .merge_ontos import merge_ontos
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)


def create_pack(
        content_path,
        drive_ids,
        lang,
        mode="local",
        line_mode="chunk",
        subs=None,
        l_colors=None,
        pos=None,
        levels=None,
        legend=None
):
    if not subs:
        subs = [
            "1 docx-raw",
            "2 docx-text-only",
            "3 to-segment",
            "4 segmented",
            "5 to-tag",
        ]

    path_ids = [(content_path / subs[i], drive_ids[content_path.stem][i]) for i in
                range(len(drive_ids[content_path.stem]) - 1)]
    path_ontos = (content_path.parent / 'ontos' / content_path.stem, drive_ids['ontos'])
    path_ids.append(path_ontos)
    abort = prepare_folders(content_path, subs)  # prepare the folder structure
    if abort and mode == "local":
        # st.write(
        'Exiting: "content" folder did not exist. Please add some files to segment and rerun.'
    # )

    # upload 0

    path = "/home/lungsang/Desktop/levelpack-UI/content/A0/1 docx-raw/"

    folder = '1tuQxaiDOdbfv1JHXNAln2nbq1IvBOrmP'

    file_list = drive.ListFile({'q': f"'{folder}' in parents and trashed=false"}).GetList()
    for index, file in enumerate(file_list):
        print(index + 1, 'file Downloaded : ', file['title'])
        file.GetContentFile(path + file['title'])

    st.subheader("A. upload raw data")
    data_file = st.file_uploader("", type=["docx"])

    with open(os.path.join("/home/lungsang/Desktop/levelpack-UI/content/A0/1 docx-raw", data_file.name),
              "wb") as f:
        f.write(data_file.getbuffer())

    st.success("File uploaded in content/A0/1 docx-raw")

    if mode == "local":
        create_pack_local(path_ids, lang=lang, line_mode=line_mode, l_colors=l_colors, pos=pos, levels=levels,
                          legend=legend, ontos=path_ontos)
    elif mode == "drive":
        create_pack_local(path_ids, lang=lang, line_mode=line_mode, l_colors=l_colors, pos=pos, levels=levels,
                          legend=legend, ontos=path_ontos)
        upload_to_drive(drive_ids)
    elif mode == "download":
        download_drive(path_ids)
    elif mode == "upload":
        upload_to_drive(drive_ids)
    else:
        raise ValueError('either one of "local", "drive", "download" and "upload".')


def create_pack_local(path_ids, lang="bo", line_mode="chunk", l_colors=None, pos=None, levels=None, legend=None,
                      ontos=None):
    state, resources = current_state(path_ids)
    new_files = []
    T = Tokenizer(lang=lang)
    tok = None
    has_totag_unfinished = False
    has_ontos_unfinished = False

    for file, steps in state.items():
        st.write(file)
        cur = 1
        while cur <= 7 and cur in steps and steps[cur]:
            cur += 1

        # 1. convert raw .docx files to text only containing raw text
        if cur == 2:
            # st.write("\tconverting to simple text...")
            in_file = steps[cur - 1]
            out_file = path_ids[cur - 1][0] / (in_file.stem + '_textonly.docx')
            convert2plaintxt(in_file, out_file)
            new_files.append(out_file)

            # 2. mark all text to be extracted using a given style
            # st.write('\t Please download the file and apply the style to all text to be extracted.')

        # download 1
        st.subheader("B. please download the file to style and upload again for segmentation.")
        data = open("/home/lungsang/Desktop/levelpack-UI/content/A0/2 docx-text-only/A0.02-vocab_textonly.docx", "rb") \
            .read()

        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)

        st.download_button('Download Here', decoded, "A0.02-vocab_textonly.docx", key='01')

        # st.success("File Downloaded")

        # upload 1
        data_file = st.file_uploader("", key='02', type=["docx"])

        with open(os.path.join("/home/lungsang/Desktop/levelpack-UI/content/A0/2 docx-text-only", data_file.name),
                  "wb") as f:
            f.write(data_file.getbuffer())

        st.success("File uploaded in content/A0/2 docx-text-only")

        # 3. extract all marked text
        out_file = None
        if cur == 3:
            # st.write("\textracting all text and segmenting it")
            in_file = steps[cur - 1]
            out_file = path_ids[cur - 1][0] / (in_file.stem.split('_')[0] + '_tosegment.txt')
            extract_content(in_file, out_file)
            new_files.append(out_file)
            cur += 1  # incrementing so that segmentation happens right after

        # 5. segment the selected input
        if cur == 4:
            # st.write("\tsegmenting...")
            in_file = steps[cur - 1] if steps[cur - 1] else out_file
            out_file = path_ids[cur - 1][0] / (in_file.stem.split('_')[0] + "_segmented.txt")
            if not tok:
                tok = T.set_tok()
            T.tok_file(tok, in_file, out_file)
            new_files.append(out_file)

            # 6. manually correct the segmentation
            # st.write("\tPlease download the file and manually correct the segmentation.")

        # download 2
        st.subheader("C. please manually correct the segmentation and upload again.")
        data = open("/home/lungsang/Desktop/levelpack-UI/content/A0/4 segmented/A0.02-vocab_segmented.txt",
                    "rb").read()

        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)

        st.download_button('Download Here', decoded, "A0.02-vocab_segmented.txt", key='02')

        # upload 2
        data_file = st.file_uploader("", key='03', type=["txt"])

        with open(os.path.join("/home/lungsang/Desktop/levelpack-UI/content/A0/4 segmented", data_file.name),
                  "wb") as f:
            f.write(data_file.getbuffer())

        st.success("File uploaded in content/A0/4segmented")

        # 7. create the _totag.xlsx in to_tag from the segmented .txt file from segmented
        if cur == 5:
            if not has_totag_unfinished:
                # st.write("\ncreating the file to tag...")
                in_file = steps[cur - 1]
                out_file = path_ids[cur - 1][0] / (
                        in_file.stem.split("_")[0] + "_totag.xlsx"
                )
                tmp_onto = ontos[0] / (out_file.stem.split('_')[0] + '_partial.yaml')

                finalized_ontos = ontos[0].parent
                current_ontos = path_ids[5][0]
                # generate partial ontos from the tagged chunks
                if out_file.is_file():
                    onto_from_tagged(out_file, tmp_onto, finalized_ontos, current_ontos, ontos[0], legend)

                # switch line_mode to chunk if filename ends with "vocab"
                contextual_line_mode = ''
                if file.endswith('vocab'):
                    contextual_line_mode += 'chunk'
                else:
                    contextual_line_mode += line_mode

                # create totag
                has_totag_unfinished = generate_to_tag(in_file, out_file, finalized_ontos, current_ontos, pos, levels,
                                                       contextual_line_mode, l_colors)

                new_files.append(out_file)
                # 8. manually POS tag the segmented text
                # print(
                "\t--> Please manually tag new words with their POS tag and level. (words not tagged will be ignored)"
                # )
                # st.write("Please download the file and manually tag new words with their POS tag and level")

        # download 3
        st.subheader("D. please tag new words with their POS tag and level")
        data = open("/home/lungsang/Desktop/levelpack-UI/content/A0/5 to-tag/A0.02-vocab_totag.xlsx",
                    "rb").read()

        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)

        st.download_button('Download Here', decoded, "A0.02-vocab_totag.xlsx", key='03')

        # upload 3

        data_file = st.file_uploader("", key='04', type=["xlsx"])

        with open(os.path.join("/home/lungsang/Desktop/levelpack-UI/content/A0/5 to-tag", data_file.name),
                  "wb") as f:
            f.write(data_file.getbuffer())

        st.success("File uploaded in content/A0/5 to-tag")

        # download 4
        st.subheader("E. please download the tagged file for additional tagging")
        data = open("/home/lungsang/Desktop/levelpack-UI/content/A0/5 to-tag/A0.02-vocab_totag.xlsx",
                    "rb").read()

        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)

        st.download_button('Download Here', decoded, "A0.02-vocab_totag.xlsx", key='04')

        # upload 4

        data_file = st.file_uploader("", key='05', type=["xlsx"])

        with open(os.path.join("/home/lungsang/Desktop/levelpack-UI/content/A0/5 to-tag", data_file.name),
                  "wb") as f:
            f.write(data_file.getbuffer())

        st.success("File uploaded in content/A0/5 to-tag")

        # 9. create .yaml ontology files from tagged .xlsx files from to_tag
        if cur == 6:
            if has_ontos_unfinished:
                continue

            # st.write("\t creating the onto from the tagged file...")
            in_file = steps[cur - 1]
            out_file = path_ids[cur - 1][0] / (
                    in_file.stem.split("_")[0] + "_onto.yaml"
            )
            if not out_file.is_file():
                finalized_ontos = ontos[0].parent
                current_ontos = path_ids[5][0]
                onto_from_tagged(in_file, out_file, finalized_ontos, current_ontos, ontos[0].parent, legend)
                new_files.append(out_file)

            # removing temporary partial ontos
            tmp_onto = out_file.parent / (out_file.stem.split('_')[0] + '_partial.yaml')
            if tmp_onto.is_file():
                tmp_onto.unlink()

            # 6. manually fill in the onto
            # st.write(
            '\t--> Please integrate new words in the onto from "to_organize" sections and add synonyms.'
        # )
        has_ontos_unfinished = True

        # download 5

        st.subheader("F. please edit the onto file and upload again.")
        data = open("/home/lungsang/Desktop/levelpack-UI/content/ontos/A0/A0.02-vocab_onto.yaml",
                    "rb").read()

        encoded = base64.b64encode(data)
        decoded = base64.b64decode(encoded)

        st.download_button('Download Here', decoded, "A0.02-vocab_onto.yaml", key='04')

        # upload 5
        data_file = st.file_uploader("", key='05', type=["yaml"])

        with open(os.path.join("/home/lungsang/Desktop/levelpack-UI/content/ontos/A0", data_file.name),
                  "wb") as f:
            f.write(data_file.getbuffer())

        st.success("File uploaded in content/ontos/A0/")

    # 10. merge into the level onto
    # check that all the raw docx files have corresponding ontos
    if sorted([p.stem for p in path_ids[0][0].glob('*.docx')]) == sorted(
            [p.stem.split('_')[0] for p in path_ids[5][0].glob('*_onto.yaml')]):
        in_path = path_ids[5][0]
        out_file = in_path.parent / (in_path.stem + '_onto.yaml')
        if not out_file.is_file():
            # st.write("\tmerging produced ontos into the level onto...")
            merge_ontos(in_path, out_file)
            new_files.append(out_file)

    # 11. merge all level ontos into a single master onto
    level_ontos = sorted([o for o in ontos[0].parent.glob('*.yaml') if not o.stem.startswith('master')])
    master = ontos[0].parent / 'master_onto.yaml'
    if not master.is_file():
        # st.write('\tcreating master onto...')
        merge_ontos(level_ontos, master)

    write_to_upload(new_files)

    # download 6 (master onto)
    data = open("/home/lungsang/Desktop/levelpack-UI/content/ontos/master_onto.yaml",
                "rb").read()

    encoded = base64.b64encode(data)
    decoded = base64.b64decode(encoded)

    st.download_button('Download the master onto here', decoded, "master_onto.yaml", key='04')


def current_state(paths_ids):
    state = {}
    stems = []  # for ontos_path

    # workflow files
    file_type = {
        "1 docx-raw": ".docx",
        "2 docx-text-only": ".docx",
        "3 to-segment": ".txt",
        "4 segmented": ".txt",
        "5 to-tag": ".xlsx",
        "ontos": ".yaml",
    }
    resources = {}
    for path, _ in paths_ids:
        sorted_files = sorted(list(path.glob("*")))
        for f in sorted_files:
            if path.parts[-2] != 'ontos' and f.suffix != file_type[path.stem]:  # 5 first steps
                continue
            elif path.parts[-2] == 'ontos' and f.suffix != file_type[path.parts[-2]]:  # 6th step
                continue
            # test chunks are all processed
            if path.stem.startswith('5'):
                chunks_conf = f.parent / (f.stem.split('_')[0] + '.config')
                if chunks_conf.is_file():
                    config = yaml.safe_load(chunks_conf.read_text())
                    if 'todo' in config.values():
                        continue

            # ignore the partial ontos
            if path.parts[-2] == 'ontos':
                if f.stem.endswith('partial'):
                    continue

            # add file to state
            stem = f.stem.split("_")[0]
            if stem not in stems:
                stems.append(stem)
            if stem not in state:
                state[stem] = {i: None for i in range(1, len(paths_ids) + 1)}
            if path.parts[-2] != 'ontos':
                step = int(f.parts[-2][0])
            else:
                step = 6
            state[stem][step] = f

            # add onto files to resources

    return state, resources


def write_to_upload(files):
    file = Path("to_upload.txt")
    if not file.is_file():
        file.write_text("")

    content = file.read_text().strip().split("\n")
    files = [str(f) for f in files]
    for f in files:
        if f not in content:
            content.append(f)

    file.write_text("\n".join(content))


def prepare_folders(content_path, sub_folders):
    missing = False
    # root
    if not content_path.is_dir():
        missing = True
        # st.write(f'folder "{content_path}" does not exist. Creating it...')
        content_path.mkdir()

    # workflow subfolders
    for sub in sub_folders:
        if not (content_path / sub).is_dir():
            print(f'folder "{(content_path / sub)}" does not exist. Creating it...')
            (content_path / sub).mkdir()

    # ontos folder
    onto_path = content_path.parent / 'ontos'
    if not onto_path.is_dir():
        missing = True
        print(f'folder "{onto_path}" does not exist. Creating it...')
        onto_path.mkdir()

    level_onto_path = onto_path / content_path.stem
    if not level_onto_path.is_dir():
        missing = True
        print(f'folder "{level_onto_path}" does not exist. Creating it...')
        level_onto_path.mkdir()
    return missing
