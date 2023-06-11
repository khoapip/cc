#!/bin/bash

install_docker() {
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        # Install Docker
        echo "Installing Docker..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://get.docker.com -o get-docker.sh
            sh get-docker.sh
            sudo usermod -aG docker $USER
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # Mac OSX
            brew install --cask docker
        else
            echo "Unsupported OS"
            exit 1
        fi
        echo "Docker has been installed successfully"
    else
        echo "Docker is already installed"
    fi
}

install_bacalhau() {
    # Install Bacalhau
    echo "Installing Bacalhau..."
    curl -sL https://get.bacalhau.org/install.sh | bash
}

install_symato_contribute() {
    # Set the URL of the remote script on GitHub
    github_script_url="https://raw.githubusercontent.com/telexyz/cc/main/symato-contribute.sh"

    # Set the name of the script
    script_name="symato-contribute"

    # Download the script from GitHub
    curl -o $script_name $github_script_url

    # Make the script executable
    chmod +x $script_name

    # Move the script to /usr/local/bin
    sudo mv $script_name /usr/local/bin/
    
    echo "Install symato-contribute completed!"
}

install_completed() {
    echo "  #####  #     # #     #    #    ####### ####### "
    echo " #     #  #   #  ##   ##   # #      #    #     # "
    echo " #         # #   # # # #  #   #     #    #     # "
    echo "  #####     #    #  #  # #     #    #    #     # "
    echo "       #    #    #     # #######    #    #     # "
    echo " #     #    #    #     # #     #    #    #     # "
    echo "  #####     #    #     # #     #    #    ####### "

    echo "We for your willingness to join a hand with Symato Community"
    echo "On your terminal, run \"symato-contribute\" to get started!"
}

# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------

install_docker
install_bacalhau
install_symato_contribute
install_completed
