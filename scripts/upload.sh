#!/bin/bash
#
# IPFS Constellation Upload Script
# Upload files to your Constellation cluster
#
# Usage:
#   ./upload.sh <file_or_directory>
#   ./upload.sh myfile.txt
#   ./upload.sh ./my-folder/
#
# Environment variables:
#   CONSTELLATION_API_URL - API endpoint (required)
#   CONSTELLATION_API_KEY - API key for authentication (optional)
#   CONSTELLATION_USERNAME - Username for basic auth (optional)
#   CONSTELLATION_PASSWORD - Password for basic auth (optional)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default API URL (can be overridden)
API_URL="${CONSTELLATION_API_URL:-https://ubitquityx.com/IPFS_Constellation/api}"

print_usage() {
    echo "IPFS Constellation Upload Script"
    echo ""
    echo "Usage: $0 [OPTIONS] <file_or_directory>"
    echo ""
    echo "Options:"
    echo "  -u, --url URL       API endpoint URL (default: \$CONSTELLATION_API_URL)"
    echo "  -k, --key KEY       API key for authentication"
    echo "  -w, --wrap          Wrap files in a directory"
    echo "  -p, --pin           Pin after upload (default: true)"
    echo "  -q, --quiet         Suppress output except CID"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CONSTELLATION_API_URL    - API endpoint"
    echo "  CONSTELLATION_API_KEY    - API key"
    echo "  CONSTELLATION_USERNAME   - Basic auth username"
    echo "  CONSTELLATION_PASSWORD   - Basic auth password"
    echo ""
    echo "Examples:"
    echo "  $0 myfile.txt"
    echo "  $0 --url https://api.example.com ./my-folder/"
    echo "  CONSTELLATION_API_KEY=xxx $0 document.pdf"
}

log_info() {
    if [ "$QUIET" != "true" ]; then
        echo -e "${GREEN}[INFO]${NC} $1"
    fi
}

log_warn() {
    if [ "$QUIET" != "true" ]; then
        echo -e "${YELLOW}[WARN]${NC} $1"
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Parse command line arguments
WRAP="false"
PIN="true"
QUIET="false"
API_KEY=""
FILE_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -k|--key)
            API_KEY="$2"
            shift 2
            ;;
        -w|--wrap)
            WRAP="true"
            shift
            ;;
        -p|--pin)
            PIN="true"
            shift
            ;;
        --no-pin)
            PIN="false"
            shift
            ;;
        -q|--quiet)
            QUIET="true"
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
        *)
            FILE_PATH="$1"
            shift
            ;;
    esac
done

# Validate input
if [ -z "$FILE_PATH" ]; then
    log_error "No file or directory specified"
    print_usage
    exit 1
fi

if [ ! -e "$FILE_PATH" ]; then
    log_error "File or directory not found: $FILE_PATH"
    exit 1
fi

# Check for curl
if ! command -v curl &> /dev/null; then
    log_error "curl is required but not installed"
    exit 1
fi

# Build authentication headers
AUTH_HEADER=""
if [ -n "$API_KEY" ] || [ -n "$CONSTELLATION_API_KEY" ]; then
    KEY="${API_KEY:-$CONSTELLATION_API_KEY}"
    AUTH_HEADER="-H \"Authorization: Bearer $KEY\""
elif [ -n "$CONSTELLATION_USERNAME" ] && [ -n "$CONSTELLATION_PASSWORD" ]; then
    AUTH_HEADER="-u \"$CONSTELLATION_USERNAME:$CONSTELLATION_PASSWORD\""
fi

# Build URL with query parameters
UPLOAD_URL="${API_URL}/api/v0/add?pin=${PIN}&wrap-with-directory=${WRAP}"

log_info "Uploading to: $API_URL"
log_info "File/Directory: $FILE_PATH"
log_info "Pin: $PIN"

# Perform upload
if [ -d "$FILE_PATH" ]; then
    log_info "Uploading directory recursively..."

    # For directories, we need to add each file
    RESPONSE=$(find "$FILE_PATH" -type f -exec curl -s -X POST \
        ${AUTH_HEADER} \
        -F "file=@{}" \
        "${UPLOAD_URL}&recursive=true" \;)
else
    log_info "Uploading file..."

    if [ -n "$AUTH_HEADER" ]; then
        RESPONSE=$(eval curl -s -X POST \
            $AUTH_HEADER \
            -F "file=@$FILE_PATH" \
            "$UPLOAD_URL")
    else
        RESPONSE=$(curl -s -X POST \
            -F "file=@$FILE_PATH" \
            "$UPLOAD_URL")
    fi
fi

# Check for errors
if echo "$RESPONSE" | grep -q "error"; then
    log_error "Upload failed!"
    echo "$RESPONSE" | jq -r '.Message // .error // .' 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# Extract CID from response
CID=$(echo "$RESPONSE" | jq -r '.Hash // .cid // empty' 2>/dev/null | tail -1)

if [ -z "$CID" ]; then
    # Try to parse as newline-delimited JSON (IPFS style)
    CID=$(echo "$RESPONSE" | tail -1 | jq -r '.Hash // .cid // empty' 2>/dev/null)
fi

if [ -z "$CID" ]; then
    log_error "Could not extract CID from response"
    echo "$RESPONSE"
    exit 1
fi

# Success output
if [ "$QUIET" = "true" ]; then
    echo "$CID"
else
    echo ""
    echo -e "${GREEN}Upload successful!${NC}"
    echo "================================"
    echo -e "CID: ${YELLOW}$CID${NC}"
    echo ""
    echo "Access your content:"
    echo "  Gateway: https://gateway.ubitquityx.com/ipfs/$CID"
    echo "  IPFS:    ipfs://$CID"
    echo ""
    echo "Verify pin status:"
    echo "  constellation-cli pin ls $CID"
fi
