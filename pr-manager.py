from huggingface_hub import HfApi
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str,
                        help='HuggingFace write token', required=True)
    parser.add_argument('--repo_id', type=str,
                        help='HuggingFace repo_id', required=True)
    # allow author: list or str
    parser.add_argument('--authors', type=str, nargs='+',
                        help='HuggingFace authors', default=[])
    args = parser.parse_args()
    return args

# run this code to merge all the PR based author username
# example run: python .\PR-manager.py --token yourtoken --repo_id Symato/cc --authors khunglong robot ninja
if __name__ == '__main__':
    args = parse_args()
    authors = args.authors
    if authors:
        print(f"Allow authors: {authors}")

    api = HfApi(token=args.token)

    for discuss in api.get_repo_discussions(repo_id=args.repo_id, repo_type='dataset'):
        if not (discuss.is_pull_request and discuss.status == 'open'):
            continue
        if discuss.author not in authors:
            continue
        api.merge_pull_request(
            repo_id='Symato/cc',
            discussion_num=discuss.num,
            repo_type='dataset',
        )
        print(
            f"merged {discuss.num}\n{discuss.title}\nAuthor: {discuss.author}")
        print('='*20)
