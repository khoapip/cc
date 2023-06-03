# SYMATO CC
SYMATO CC is a crowd computing project that allows anyone to join and contribute to the preprocessing of Vietnamese Common Crawl data. By using our symato-contribute script, you can easily set up your local machine to start serving and contributing to the project.

## Get Started
To get started, you’ll need to install the symato-contribute script and its dependencies on your local Linux/MacOS or WSL machine. This can be done by running the following command in your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/telexyz/cc/main/symato-contribute.sh | sudo bash
```

The script requires sudo permission to install the following tools:

- Bacalhau Binary: This tool is used for distributed jobs.
- Docker: This tool provides an isolated execution environment.
- AWS CLI: This tool is required for quick access to the CommonCrawl data via the S3 protocol, as required by Bacalhau.

## Start Serving
Once you have installed the symato-contribute script and its dependencies, you can start serving and contributing to the project by running the following command in your terminal:

```bash
symato-contribute
```

This will start the SYMATO CC crowd computing process on your local machine. You can now contribute to the preprocessing of Vietnamese Common Crawl data.

Thank you for joining and contributing to SYMATO CC!
