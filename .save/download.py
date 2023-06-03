from parfive import Downloader


if __name__ == '__main__':
    urls = ['https://data.commoncrawl.org/crawl-data/CC-MAIN-2023-14/segments/1679296943471.24/warc/CC-MAIN-20230320083513-20230320113513-00000.warc.gz']
    # max_splits: càng lớn thì càng nhanh
    # max_conn: số file download cùng lúc
    dl = Downloader(overwrite=True, max_splits=16, max_conn=4)

    for url in urls:
        dl.enqueue_file(url, path='data/')
    dl.download()
