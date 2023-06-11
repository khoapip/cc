import trafilatura
from fastwarc.warc import ArchiveIterator
import fasttext
import pypandoc
import bs4 as bs
import pandas as pd
import multiprocessing as mp
import argparse
import os
from huggingface_hub import HfApi, CommitOperationAdd
import requests
from downloader import Downloader

# disable fasttext warning
fasttext.FastText.eprint = lambda x: None

# load fasttext model: https://fasttext.cc/docs/en/language-identification.html
model = fasttext.load_model('./lid.176.bin')


def extract_text(data):
    content = data['content']
    headers = data['headers']

    text = trafilatura.extract(content)
    if text is None:
        return None

    lang = model.predict(text.replace('\n', '. '))[0][0].split('__')[-1]
    if lang != 'vi':
        return None

    soup = bs.BeautifulSoup(content, 'lxml')

    soup = soup.find('main')
    if not soup:
        soup = bs.BeautifulSoup(content, 'lxml')

    for tag in ['header', 'footer', 'script', 'style']:
        for div in soup.find_all(tag):
            div.decompose()

    html_string = soup.prettify()

    markdown = pypandoc.convert_text(
        html_string, to="gfm+hard_line_breaks-raw_html",
        format='html', extra_args=['--quiet'])

    return {
        'text': text,
        'markdown': markdown,
        'headers': headers
    }


def extract_warc(file):
    tasks = []
    items = []
    len_tasks = 0

    with mp.Pool(args.num_workers) as p:
        for record in ArchiveIterator(open(file, 'rb'), func_filter=lambda r: r.headers.get('WARC-Identified-Payload-Type') == 'text/html'):

            content = record.reader.read()

            headers = {
                'headers': record.headers.asdict(),
                'http_headers': record.http_headers.asdict()
            }

            tasks.append({
                'content': content,
                'headers': headers
            })
            len_tasks += 1

            if len(tasks) == 3 * 1024:
                for item in p.imap_unordered(extract_text, tasks):
                    if item is not None:
                        items.append(item)
                tasks = []  # reset

        # Xử lý chỗ task còn lại
        for item in p.imap_unordered(extract_text, tasks):
            if item is not None:
                items.append(item)

    # Ghi items ra parquet file
    df = pd.DataFrame(items)
    output_parquet = os.path.join(
        '/outputs', os.path.basename(file).replace('.warc.gz', '.parquet'))
    df.to_parquet(output_parquet)

    print("File name: ", file)
    print("Total pages: ", len_tasks)
    print("Total Vietnamese pages: ", len(df))
    print("Output: ", output_parquet)
    print("====================================")
    result = {
        'file_path': output_parquet,
        'total_page': len_tasks,
        'vi_page': len(df)
    }
    return result


def get_token():
    print("Retrieving Hugging Face token...")

    # Get HuggingFace Token by Node's IP address
    server_url = f'https://symato.vysma.cloud/webhook/token-by-ip'
    response = requests.get(server_url)
    data = response.json()
    discord_handle = data['discord']
    hf_token = data['hf_token']
    return discord_handle, hf_token


def to_huggingface(repo_id, item, dump_name):
    discord_handle, token = get_token()
    print('Uploading to huggingface hub...')
    api = HfApi()
    operations = []

    description = ''

    segment_name = os.path.basename(item['file_path']).split("-")
    file_name = segment_name[-1]
    segment_name = "-".join(segment_name[:-1])
    path_in_repo = '{}/{}/{}'.format(dump_name, segment_name, file_name)
    operations.append(
        CommitOperationAdd(
            path_in_repo=path_in_repo,
            path_or_fileobj=item['file_path'],
        )
    )
    description += "\n- {}: {} vi page out of {} pages".format(
        path_in_repo, item['vi_page'], item['total_page'])
    try:
        api.create_commit(
            repo_id=repo_id,
            operations=operations,
            commit_message='{} submit {}'.format(discord_handle, path_in_repo),
            commit_description=description,
            repo_type='dataset',
            create_pr=False,
            token=token
        )
    except Exception as e:
        # if cant push direct, make a PR
        print(e)
        api.create_commit(
            repo_id=repo_id,
            operations=operations,
            commit_message='{} submit {}'.format(discord_handle, path_in_repo),
            commit_description=description,
            repo_type='dataset',
            create_pr=True,
            token=token
        )
    print('Done!')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str,
                        help='HTTP Link Of WARC file', required=True)
    parser.add_argument(
        '--dump', type=str, help='Dump name of the warc file belong to', required=True)
    parser.add_argument('--repo_id', type=str,
                        help='Repo to create PR', required=True)
    n_workers = mp.cpu_count() - 1 if mp.cpu_count() > 1 else 1
    parser.add_argument('--num_workers', type=int, default=n_workers)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    obj = Downloader(args.url, args.num_workers)
    obj.start_download()
    print(obj.get_metadata())
    print(obj.get_remote_crc32c())
    print(obj.get_downloaded_crc32c())

    input_file = os.path.basename(obj.url)
    print("Start processing WARC...")
    output_parquet = extract_warc(input_file)
    to_huggingface(args.repo_id, output_parquet, args.dump)
