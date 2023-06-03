import trafilatura
from fastwarc.warc import ArchiveIterator
import fasttext
from tqdm import tqdm
import pypandoc
import bs4 as bs
import pandas as pd
import multiprocessing as mp
import argparse
import os
from huggingface_hub import HfApi, CommitOperationAdd
import requests

# disable fasttext warning
fasttext.FastText.eprint = lambda x: None

# load fasttext model: https://fasttext.cc/docs/en/language-identification.html
model = fasttext.load_model('./lid.176.bin')

def extract_text(content):
    text = trafilatura.extract(content)
    if text is None:
        return None
    lang = model.predict(text.replace('\n', '. '))[0][0].split('__')[-1]
    if lang == 'vi':
        soup = bs.BeautifulSoup(content, 'lxml')
        if soup.find('body'):
            soup = soup.find('body')
        if soup.find('main'):
            soup = soup.find('main')
        list_Tags = ['header', 'footer', 'script', 'style']
        for tag in list_Tags:
            for div in soup.find_all(tag):
                div.decompose()
        html_string = soup.prettify()
        markdown = pypandoc.convert_text(
            html_string, to="gfm+hard_line_breaks-raw_html", format='html', extra_args=['--quiet'])
        item = {'text': text, 'markdown': markdown, }
        return item
    else:
        return None
      
def extract_warc(file):
    tasks = []
    for record in tqdm(ArchiveIterator(open(file, 'rb'), func_filter=lambda r: r.headers.get('WARC-Identified-Payload-Type') == 'text/html'),
                       desc=f'Loading {file}'):
        content = record.reader.read()
        tasks.append(content)

    items = []
    with mp.Pool(args.num_workers) as p:
        for item in tqdm(p.imap(extract_text, tasks), total=len(tasks), desc='Extracting text'):
            if item is not None:
                items.append(item)
    df = pd.DataFrame(items)

    output_parquet = os.path.join('/outputs', os.path.basename(file).replace('.warc.gz', '.parquet'))
    df.to_parquet(output_parquet)
    print("File name: ", file)
    print("Total pages: ", len(tasks))
    print("Total Vietnamese pages: ", len(df))
    print("Output: ", output_parquet)
    print("====================================")
    result = {
        'file_path': output_parquet,
        'total_page': len(tasks),
        'vi_page': len(df)
    }
    return result

def get_token():
    print("Retrieving Hugging Face token...")
    # Get IP address of decentralized node.
    ip_response = requests.get('https://ifconfig.co/json')
    ip_data = ip_response.json()
    ip_address = ip_data['ip']

    # Get Discord handle by IP address
    server_url = f'https://symato.vysma.cloud/webhook/token-by-ip?ip={ip_address}'
    response = requests.get(github_url)
    data = response.json()
    discord_handle = data['discord']
    hf_token = data['hf_token']
    return hf_token

def to_huggingface(item, dump_name):
    token = get_token()
    print('Uploading to huggingface hub...')
    api = HfApi()
    operations = []

    description = ''
    
    path_in_repo = '{}/{}'.format(dump_name,
                                  os.path.basename(item['file_path']))
    operations.append(
        CommitOperationAdd(
            path_in_repo=path_in_repo,
            path_or_fileobj=item['file_path'],
        )
    )
    description += "\n- {}: {} vi page out of {} pages".format(
        path_in_repo, item['vi_page'], item['total_page'])

    api.create_commit(
        repo_id='Symato/CC-VI',
        operations=operations,
        commit_message='Add parquet files to dumps {}'.format(dump_name),
        commit_description=description,
        repo_type='dataset',
        create_pr=True,
        token=token
    )
    print('Done!')
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', type=str,
                        help='Dump name of the warc file belong to', required=True)
    parser.add_argument('--input_file', type=str,
                        help='HTTP Link Of WARC file', required=True)
    n_workers = mp.cpu_count() - 1 if mp.cpu_count() > 1 else 1
    parser.add_argument('--num_workers', type=int, default=n_workers)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    input_local_file = os.path.join("/inputs", args.input_file)
    output_parquet = extract_warc(input_local_file)
    if len(args.token) > 0:
        to_huggingface(output_parquet, args.dump)
