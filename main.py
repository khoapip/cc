import trafilatura
from fastwarc.warc import ArchiveIterator
import fasttext
from tqdm import tqdm
import pypandoc
import bs4 as bs
import polars as pl
import multiprocessing as mp
import argparse
import os
from parfive import Downloader
from huggingface_hub import HfApi, CommitOperationAdd

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
        item = {'text': text, 'markdown': markdown, 'headers': headers}
        return item
    else:
        return None


def download_file(urls_file):
    urls = open(urls_file, 'r').readlines()
    print('Total files:', len(urls))
    urls = ['https://data.commoncrawl.org/' + url.strip() for url in urls]
    # max_splits: càng lớn thì càng nhanh
    # max_conn: số file download cùng lúc
    dl = Downloader(max_splits=20, max_conn=2)
    for url in urls:
        dl.enqueue_file(url, path='warc/')
    result = dl.download()
    return result


def extract_warc(files):
    results = []
    for file in files:
        tasks = []
        for record in tqdm(ArchiveIterator(open(file, 'rb'), func_filter=lambda r: r.headers.get('WARC-Identified-Payload-Type') == 'text/html'),
                           desc=f'Loading {file}'):
            content = record.reader.read()
            headers = {
                'headers': record.headers.asdict(),
                'http_headers': record.http_headers.asdict()
            }
            tasks.append({
                'content': content,
                'headers': headers
            })
        items = []
        with mp.Pool(args.num_workers) as p:
            for item in tqdm(p.imap_unordered(extract_text, tasks), total=len(tasks), desc='Extracting text'):
                if item is not None:
                    items.append(item)
        df = pl.DataFrame(items)
        output = os.path.join(output_folder,
                              os.path.basename(file).replace('.warc.gz', '.parquet'))
        df.write_parquet(output)
        result = {
            'file_path': output,
            'total_page': len(tasks),
            'vi_page': len(df)
        }
        results.append(result)
        print("File name: ", file)
        print("Total pages: ", len(tasks))
        print("Total Vietnamese pages: ", len(df))
        print("Output: ", output)
        print("====================================")
    return results


def to_huggingface(data, dump_name, token):
    print('Uploading to huggingface hub...')
    api = HfApi()
    operations = []

    description = ''

    for item in data:
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
    parser.add_argument('--path_file', type=str,
                        help='LIST path of WARC file', required=True)
    parser.add_argument('--output', type=str,
                        default='parquet', help='Output folder')
    parser.add_argument('--num_workers', type=int, default=mp.cpu_count())
    # huggingface token
    parser.add_argument('--token', type=str, help='Huggingface token')
    parser.add_argument('--dump', type=str,
                        help='Dump name of the warc file belong to', required=True)
    return parser.parse_args()


if __name__ == '__main__':
    pypandoc.download_pandoc()
    print('Pandoc version:', pypandoc.get_pandoc_version())
    print('Trafilatura version:', trafilatura.__version__)
    args = parse_args()
    output_folder = args.output
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    files = download_file(args.path_file)
    results = extract_warc(files)
    if len(results) > 0 and args.token:
        to_huggingface(results, args.dump, args.token)

