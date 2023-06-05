#!/usr/bin/env bash

# BACALHAU CLI location
: "${BACALHAU_INSTALL_DIR:="/usr/local/bin"}"

# sudo is required to copy binary to BACALHAU_INSTALL_DIR for linux
: "${USE_SUDO:="false"}"

# Option to download pre-releases
: "${PRE_RELEASE:="false"}"

# Http request CLI
BACALHAU_HTTP_REQUEST_CLI=curl

# GitHub Organization and repo name to download release
GITHUB_ORG=telexyz
GITHUB_REPO=cc

# BACALHAU CLI filename
BACALHAU_CLI_FILENAME=bacalhau

BACALHAU_CLI_FILE="${BACALHAU_INSTALL_DIR}/${BACALHAU_CLI_FILENAME}"

installDocker() {
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Installing Docker now..."
        # Download the script and execute it
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        
        # sudo usermod -aG docker $USER
        
        echo "Please logout and relogin or restart your machine before serving with Symato!"

        # Remove the script
        rm get-docker.sh

        echo "Docker has been installed successfully"
    else
        echo "Docker is already installed"
    fi
}

installAWSCLI() {
    if ! command -v aws &> /dev/null; then
        echo "AWS CLI is not installed. Installing Docker now..."
        # Install Unzip
        sudo apt-get install -y unzip jq

        # Download AWS CLI package
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

        # Unzip the package
        unzip awscliv2.zip

        # Install AWS CLI
        sudo ./aws/install --update -i /usr/local/aws-cli -b $BACALHAU_INSTALL_DIR

        # Clean up downloaded zip file
        rm awscliv2.zip
        rm -rf ./aws
     else
         echo "AWS CLI is already installed!"
     fi
}

getSystemInfo() {
    ARCH=$(uname -m)
    case $ARCH in
        armv7*) ARCH="arm" ;;
        aarch64) ARCH="arm64" ;;
        x86_64) ARCH="amd64" ;;
    esac

    OS=$(eval "echo $(uname)|tr '[:upper:]' '[:lower:]'")

    # Most linux distro needs root permission to copy the file to /usr/local/bin
    if [ "$OS" == "linux" ] && [ "$BACALHAU_INSTALL_DIR" == "/usr/local/bin" ]; then
        USE_SUDO="true"
    # Darwin needs permission to copy the file to /usr/local/bin
    elif [ "$OS" == "darwin" ] && [ "$BACALHAU_INSTALL_DIR" == "/usr/local/bin" ]; then
        USE_SUDO="true"
    fi
}

verifySupported() {
    local supported=(linux-amd64 linux-arm64 darwin-amd64 darwin-arm64)
    local current_osarch="${OS}-${ARCH}"

    for osarch in "${supported[@]}"; do
        if [ "$osarch" == "$current_osarch" ]; then
            echo "Your system is ${OS}_${ARCH}"
            return
        fi
    done

    echo "No prebuilt binary for ${current_osarch}"
    exit 1
}

runAsRoot() {
    local CMD="$*"

    if [ $EUID -ne 0 ] && [ $USE_SUDO = "true" ]; then
        CMD="sudo $CMD"
    fi

    $CMD
}

checkHttpRequestCLI() {
    if type "curl" > /dev/null; then
        BACALHAU_HTTP_REQUEST_CLI=curl
    elif type "wget" > /dev/null; then
        BACALHAU_HTTP_REQUEST_CLI=wget
    else
        echo "Either curl or wget is required"
        exit 1
    fi
}

checkExistingBacalhau() {
    if [ -f "$BACALHAU_CLI_FILE" ]; then
        echo -e "\nBACALHAU CLI is detected:"
        $BACALHAU_CLI_FILE version
        echo -e "Reinstalling BACALHAU CLI - ${BACALHAU_CLI_FILE}..."
    else
        echo -e "No BACALHAU detected. Installing fresh BACALHAU CLI..."
    fi
}

getLatestRelease() {
    # /latest ignores pre-releases, see https://docs.github.com/en/rest/releases/releases#get-the-latest-release
    if [ "$PRE_RELEASE" == "true" ]; then
        echo "Installing most recent pre-release version..."
        local bacalhauReleaseUrl="https://api.github.com/repos/${GITHUB_ORG}/${GITHUB_REPO}/releases"
    else
        local bacalhauReleaseUrl="https://api.github.com/repos/${GITHUB_ORG}/${GITHUB_REPO}/releases/latest"
    fi
    local latest_release=""

    if [ "$BACALHAU_HTTP_REQUEST_CLI" == "curl" ]; then
        latest_release=$(curl -s $bacalhauReleaseUrl  | grep \"tag_name\" | grep -E -i '"v[0-9]+\.[0-9]+\.[0-9]+"' | grep -v rc | awk 'NR==1{print $2}' | sed -n 's/\"\(.*\)\",/\1/p')
    else
        latest_release=$(wget -q --header="Accept: application/json" -O - $bacalhauReleaseUrl | grep \"tag_name\" | grep -E -i '^v[0-9]+\.[0-9]+\.[0-9]+$' | grep -v rc | awk 'NR==1{print $2}' |  sed -n 's/\"\(.*\)\",/\1/p')
    fi

    ret_val=$latest_release
}
# --- create temporary directory and cleanup when done ---
setup_tmp() {
    BACALHAU_TMP_ROOT=$(mktemp -d 2>/dev/null || mktemp -d -t 'bacalhau-install.XXXXXXXXXX')
    cleanup() {
        code=$?
        set +e
        trap - EXIT
        rm -rf "${BACALHAU_TMP_ROOT}"
        exit $code
    }
    trap cleanup INT EXIT
}

downloadFile() {
    LATEST_RELEASE_TAG=$1

    BACALHAU_CLI_ARTIFACT="${BACALHAU_CLI_FILENAME}_${LATEST_RELEASE_TAG}_${OS}_${ARCH}.tar.gz"

    DOWNLOAD_BASE="https://github.com/${GITHUB_ORG}/${GITHUB_REPO}/releases/download"

    CLI_DOWNLOAD_URL="${DOWNLOAD_BASE}/${LATEST_RELEASE_TAG}/${BACALHAU_CLI_ARTIFACT}"

    CLI_TMP_FILE="$BACALHAU_TMP_ROOT/$BACALHAU_CLI_ARTIFACT"

    echo "Downloading $CLI_DOWNLOAD_URL ..."
    if [ "$BACALHAU_HTTP_REQUEST_CLI" == "curl" ]; then
        curl -SsLN "$CLI_DOWNLOAD_URL" -o "$CLI_TMP_FILE"
    else
        wget -q -O "$CLI_TMP_FILE" "$CLI_DOWNLOAD_URL"
    fi

    if [ ! -f "$CLI_TMP_FILE" ]; then
        echo "failed to download $CLI_DOWNLOAD_URL ..."
        exit 1
    fi

}

expandTarball() {
    echo "Extracting tarball ..."
    # echo "Extract tar file - $CLI_TMP_FILE to $BACALHAU_TMP_ROOT"
    tar xzf "$CLI_TMP_FILE" -C "$BACALHAU_TMP_ROOT"
}

verifyBin() {
    # openssl base64 -d -in $BACALHAU_TMP_ROOT/bacalhau.signature.sha256 -out $BACALHAU_TMP_ROOT/bacalhau.signature.sha256.decoded
    # if openssl dgst -sha256 -verify "$BACALHAU_TMP_ROOT/BACALHAU_public_file.pem" -signature $BACALHAU_TMP_ROOT/bacalhau.signature.sha256.decoded $BACALHAU_TMP_ROOT/bacalhau; then
    #     return
    # else
    #     echo "Failed to verify signature of bacalhau binary."
    #     exit 1
    # fi
    echo "NOT verifying Bin"
}


installFile() {
    local tmp_root_bacalhau_cli="$BACALHAU_TMP_ROOT/$BACALHAU_CLI_FILENAME"

    if [ ! -f "$tmp_root_bacalhau_cli" ]; then
        echo "Failed to unpack BACALHAU CLI executable."
        exit 1
    fi

    chmod o+x "$tmp_root_bacalhau_cli"
    if [ -f "$BACALHAU_INSTALL_DIR/$BACALHAU_CLI_FILENAME" ]; then
        runAsRoot rm -f "$BACALHAU_INSTALL_DIR/$BACALHAU_CLI_FILENAME"
    fi
    runAsRoot cp "$tmp_root_bacalhau_cli" "$BACALHAU_INSTALL_DIR"

    if [ -f "$BACALHAU_CLI_FILE" ]; then
        echo "$BACALHAU_CLI_FILENAME installed into $BACALHAU_INSTALL_DIR successfully."

        $BACALHAU_CLI_FILE version
    else
        echo "Failed to install $BACALHAU_CLI_FILENAME"
        exit 1
    fi
}

fail_trap() {
    result=$?
    if [ "$result" != "0" ]; then
        echo "Failed to install BACALHAU CLI"
        echo "For support, go to https://github.com/${GITHUB_ORG}/${GITHUB_REPO}"
    fi
    cleanup
    exit $result
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

cleanup() {
    if [[ -d "${BACALHAU_TMP_ROOT:-}" ]]; then
        rm -rf "$BACALHAU_TMP_ROOT"
    fi
}

installCompleted() {
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
trap "fail_trap" EXIT

getSystemInfo
verifySupported
checkExistingBacalhau
checkHttpRequestCLI

if [ -z "$1" ]; then
    echo "Getting the latest BACALHAU CLI..."
    getLatestRelease
else
    ret_val=v$1
fi

if [ -z "$ret_val" ]; then
    echo 1>&2 "Error getting latest release..."
    exit 1
fi

echo "Installing $ret_val BACALHAU CLI..."

setup_tmp
installAWSCLI
installDocker
downloadFile "$ret_val"
expandTarball
installFile
install_symato_contribute
cleanup

installCompleted
