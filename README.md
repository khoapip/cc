# SYMATO CC
SYMATO CC is a crowd computing project that allows anyone to join and contribute to the preprocessing of Vietnamese Common Crawl data. By using our symato-contribute script, you can easily set up your local machine to start serving and contributing to the project.

## Requisition

Before getting started, make sure you have the following:

- A HuggingFace account for Pull Request submission.
- PEER_ADDR and SWARM_ADDR: register your contribution with Symato in Discord.
- A PC/Laptop/VPS/Server that meets the minimum hardware requirements: at least 2 vCPUs, 2GB of RAM, and a stable internet connection.

## Get Started
To get started, you’ll need to install the symato-contribute script and its dependencies on your local Linux/MacOS or WSL machine. This can be done by running the following command in your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/telexyz/cc/main/install.sh | bash
```

The script requires sudo permission to install the following tools:

- Bacalhau Binary: This tool is used for distributed jobs.
- Docker: This tool provides an isolated execution environment.
- AWS CLI: This tool is required for quick access to the CommonCrawl data via the S3 protocol, as required by Bacalhau.
- `jq` and `unzip`: To unzip AWS and extract response from remote server.

## Start Serving
Once you have installed the symato-contribute script and its dependencies, you can start serving and contributing to the project by running the following command in your terminal:

```bash
sudo symato-contribute
# we need sudo permission inorder to make script run correctly. And sometime the script use most of CPUs to process text.
```

Sample config:
```
DISCORD_USERNAME=xxx
HF_TOKEN=hf_....
PEER_ADDR=/ip4/103.153.73.18/tcp/1235/p2p/QmSXnt5YWdvvTyTbzUKX3bVkNAXfY1u5a2dRtXuP44fjEF
SWARM_ADDR=/ip4/103.153.73.18/tcp/4001/p2p/QmbgtvLTaGYE4j4QGu7UgRhzffCq6YWQ7e7Xkc3QqWhtSt
CPU=8
MEM=8Gb
```

You will need to enter Huggingface Token, find it at https://huggingface.co/settings/tokens

This will start the SYMATO CC crowd computing process on your local machine. You can now contribute to the preprocessing of Vietnamese Common Crawl data.

## Gathered data
huggingface.co/datasets/Symato/cc/viewer/Symato--cc

Thank you for joining and contributing to SYMATO CC!
