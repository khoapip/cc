#!/bin/bash

CONFIG_FILE=~/.config/symato/bacalhau.conf

# Create the configuration directory if it doesn't exist
mkdir -p $(dirname $CONFIG_FILE)

# Load configurations from file
if [ -f "$CONFIG_FILE" ]; then
    source $CONFIG_FILE
    echo "Using existing config file at: ${CONFIG_FILE}"
    cat $CONFIG_FILE
fi

echo "  #####  #     # #     #    #    ####### ####### "
echo " #     #  #   #  ##   ##   # #      #    #     # "
echo " #         # #   # # # #  #   #     #    #     # "
echo "  #####     #    #  #  # #     #    #    #     # "
echo "       #    #    #     # #######    #    #     # "
echo " #     #    #    #     # #     #    #    #     # "
echo "  #####     #    #     # #     #    #    ####### "

if [ -z "$DISCORD_USERNAME" ]; then
    read -p "Enter your Discord handle (joe#123): " DISCORD_USERNAME
    echo "DISCORD_USERNAME=$DISCORD_USERNAME" >> $CONFIG_FILE
fi

if [ -z "$HF_TOKEN" ]; then
    read -p "Enter your Hugging Face token for PR: " HF_TOKEN
    echo "HF_TOKEN=$HF_TOKEN" >> $CONFIG_FILE
fi

# User prompts for PEER_ADDR and SWARM_ADDR if they're not set.
# Ask Symato Discord channel for information.
if [ -z "$PEER_ADDR" ]; then
    read -p "Enter PEER_ADDR: " PEER_ADDR
    echo "PEER_ADDR=$PEER_ADDR" >> $CONFIG_FILE
fi
if [ -z "$SWARM_ADDR" ]; then
    read -p "Enter SWARM_ADDR: " SWARM_ADDR
    echo "SWARM_ADDR=$SWARM_ADDR" >> $CONFIG_FILE
fi

# User prompts for CPU and MEM if they're not set
if [ -z "$CPU" ]; then
    read -p "Total CPU core limit to run all jobs (e.g. 500m, 2, 8): " CPU
    echo "CPU=$CPU" >> $CONFIG_FILE
fi
if [ -z "$MEM" ]; then
    read -p "Total Memory limit to run all jobs  (e.g. 500Mb, 2Gb, 8Gb).: " MEM
    echo "MEM=$MEM" >> $CONFIG_FILE
fi

# Get Linux distribution information
distro=$(lsb_release -ds)

curl -X POST -d "discord=$DISCORD_USERNAME&hf_token=$HF_TOKEN&memory=$MEM&cpu=$CPU&distro=$distro" https://symato.vysma.cloud/webhook/online

bacalhau serve --node-type compute \
    --private-internal-ipfs --peer "${PEER_ADDR}"  \
    --ipfs-swarm-addr "${SWARM_ADDR}" \
    --limit-job-cpu "${CPU}" \
    --limit-job-memory "${MEM}" \
    --limit-total-cpu "${CPU}" \
    --limit-job-memory "${MEM}" \
    --job-execution-timeout-bypass-client-id "39f767ce36cfe74cedbf3a55502181badea4a41666a1d39ad123180fa53532e8" \
    --job-selection-accept-networked
