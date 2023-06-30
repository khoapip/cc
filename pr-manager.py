from huggingface_hub import HfApi
from discord_webhook import DiscordWebhook
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str,
                        help='HuggingFace write token', required=True)
    parser.add_argument('--repo_id', type=str,
                        help='HuggingFace repo_id', required=True)
    parser.add_argument('--discord_webhook', type=str,
                        help='Discord Webhook', required=True)
    # allow author: list or str
    args = parser.parse_args()
    return args

# run this code to merge all the PR based author username
# example run: python .\PR-manager.py --token yourtoken --repo_id Symato/cc --authors khunglong robot ninja
if __name__ == '__main__':
    args = parse_args()
    authors = []

    with open('whitelist_authors.txt', 'r') as f:
        authors = f.readlines()

    if authors:
        authors = [author.strip() for author in authors]
        print(f"Allow authors: {authors}")

    api = HfApi(token=args.token)

    pr_list = []
    count_by_authors = {}
    print("Loading PR...")
    for discuss in api.get_repo_discussions(repo_id=args.repo_id, repo_type='dataset'):
        if not (discuss.is_pull_request and discuss.status == 'open'):
            continue
        if discuss.author not in authors:
            continue
        pr_list.append(discuss)
        count_by_authors[discuss.author] = 0

    hf_authors = {}
    
    print(f"Merging {len(pr_list)} PR...")
    for discuss in pr_list:
        try:
            if count_by_authors[discuss.author] >= 20: # Github Actions might timeout, n limit per user
                continue
            else:
                api.merge_pull_request(
                    repo_id='Symato/cc',
                    discussion_num=discuss.num,
                    repo_type='dataset',
                )
                discord_user, processed_file = discuss.title.split(" submit ")
                if not discuss.author in hf_authors:
                    hf_authors[discuss.author] = {}
                
                if not discord_user in hf_authors[discuss.author]:
                    hf_authors[discuss.author][discord_user] = []
                
                count_by_authors[discuss.author] += 1

                hf_authors[discuss.author][discord_user].append(discuss.num)
        except:
            a = 0
    
    message = ""
    print(f"Polulating webhook message...")
    for hf_author, discord_contributors in hf_authors.items():
        message += f"\n\n### :hugging: https://huggingface.co/{hf_author} đã cùng Symato chung tay góp phần xử lý **{count_by_authors[hf_author]}** CommonCrawl files:\n"
        sub_msgs = [f"- <@{discord_user}>: {len(pr_nums)} tập tin (PRs: {', '.join([ f'#{pr}' for pr in pr_nums ])})" for discord_user, pr_nums in discord_contributors.items()]
        message += "\n".join(sub_msgs)

    print(message)
    webhook = DiscordWebhook(url=args.discord_webhook, content=message)
    response = webhook.execute()
