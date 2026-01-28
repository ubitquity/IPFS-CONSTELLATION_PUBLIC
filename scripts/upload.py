#!/usr/bin/env python3
"""
IPFS Constellation Upload Script (Python)

Upload files to your Constellation cluster

Installation:
    pip install ipfshttpclient requests

Usage:
    python upload.py <file_path>
    python upload.py --url https://api.example.com myfile.txt

Environment variables:
    CONSTELLATION_API_URL - API endpoint
    CONSTELLATION_API_KEY - API key for authentication
"""

import os
import sys
import argparse
import json
from pathlib import Path

# Try to import required libraries
try:
    import requests
except ImportError:
    print("Error: requests not installed")
    print("Run: pip install requests")
    sys.exit(1)

# Optional: try ipfshttpclient for native IPFS support
IPFS_CLIENT_AVAILABLE = False
try:
    import ipfshttpclient
    IPFS_CLIENT_AVAILABLE = True
except ImportError:
    pass


class ConstellationUploader:
    """Upload files to IPFS Constellation cluster."""

    def __init__(self, api_url, api_key=None, username=None, password=None):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._setup_auth()

    def _setup_auth(self):
        """Configure authentication headers."""
        if self.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.api_key}'
        elif self.username and self.password:
            self.session.auth = (self.username, self.password)

    def upload_file(self, file_path, pin=True):
        """
        Upload a single file to the cluster.

        Args:
            file_path: Path to the file to upload
            pin: Whether to pin the content (default: True)

        Returns:
            dict with 'cid' and 'size' keys
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        url = f"{self.api_url}/api/v0/add"
        params = {'pin': str(pin).lower()}

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            response = self.session.post(url, params=params, files=files)

        response.raise_for_status()

        # Parse response (may be newline-delimited JSON)
        lines = response.text.strip().split('\n')
        result = json.loads(lines[-1])

        return {
            'cid': result.get('Hash') or result.get('cid'),
            'size': result.get('Size', 0),
            'name': result.get('Name', file_path.name)
        }

    def upload_directory(self, dir_path, pin=True, wrap=False):
        """
        Upload a directory recursively to the cluster.

        Args:
            dir_path: Path to the directory to upload
            pin: Whether to pin the content (default: True)
            wrap: Whether to wrap in a directory (default: False)

        Returns:
            dict with 'cid' and 'size' keys for the root
        """
        dir_path = Path(dir_path)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        url = f"{self.api_url}/api/v0/add"
        params = {
            'pin': str(pin).lower(),
            'recursive': 'true',
            'wrap-with-directory': str(wrap).lower()
        }

        # Collect all files
        files_to_upload = []
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(dir_path.parent)
                files_to_upload.append(
                    ('file', (str(rel_path), open(file_path, 'rb')))
                )

        try:
            response = self.session.post(url, params=params, files=files_to_upload)
            response.raise_for_status()

            # Parse response - last line contains the root CID
            lines = response.text.strip().split('\n')
            result = json.loads(lines[-1])

            return {
                'cid': result.get('Hash') or result.get('cid'),
                'size': result.get('Size', 0),
                'name': result.get('Name', dir_path.name)
            }
        finally:
            # Close all file handles
            for _, (_, f) in files_to_upload:
                f.close()

    def upload(self, path, pin=True, wrap=False):
        """
        Upload a file or directory.

        Args:
            path: Path to file or directory
            pin: Whether to pin the content
            wrap: Whether to wrap in a directory

        Returns:
            dict with upload result
        """
        path = Path(path)

        if path.is_dir():
            return self.upload_directory(path, pin=pin, wrap=wrap)
        else:
            return self.upload_file(path, pin=pin)

    def check_connection(self):
        """Test connection to the API."""
        try:
            response = self.session.post(f"{self.api_url}/api/v0/id")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False


def main():
    parser = argparse.ArgumentParser(
        description='IPFS Constellation Upload Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  CONSTELLATION_API_URL    - API endpoint
  CONSTELLATION_API_KEY    - API key
  CONSTELLATION_USERNAME   - Basic auth username
  CONSTELLATION_PASSWORD   - Basic auth password

Examples:
  python upload.py myfile.txt
  python upload.py --url https://api.example.com ./my-folder/
  CONSTELLATION_API_KEY=xxx python upload.py document.pdf
        """
    )

    parser.add_argument('path', help='File or directory to upload')
    parser.add_argument('-u', '--url',
                        default=os.environ.get('CONSTELLATION_API_URL', 'https://ubitquityx.com/IPFS_Constellation/api'),
                        help='API endpoint URL')
    parser.add_argument('-k', '--key',
                        default=os.environ.get('CONSTELLATION_API_KEY', ''),
                        help='API key for authentication')
    parser.add_argument('-w', '--wrap', action='store_true',
                        help='Wrap files in a directory')
    parser.add_argument('--no-pin', action='store_true',
                        help="Don't pin after upload")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Suppress output except CID')

    args = parser.parse_args()

    # Get credentials from environment if not provided
    username = os.environ.get('CONSTELLATION_USERNAME', '')
    password = os.environ.get('CONSTELLATION_PASSWORD', '')

    if not args.quiet:
        print('IPFS Constellation Upload')
        print('=' * 40)
        print(f'API URL: {args.url}')
        print(f'File: {args.path}')
        print(f'Pin: {not args.no_pin}')
        print()

    # Create uploader
    uploader = ConstellationUploader(
        api_url=args.url,
        api_key=args.key,
        username=username,
        password=password
    )

    # Check connection
    if not args.quiet:
        print('Checking connection...')
        if not uploader.check_connection():
            print('\033[33mWarning: Could not verify API connection\033[0m')
            print('Attempting upload anyway...')
        print()

    try:
        if not args.quiet:
            path = Path(args.path)
            if path.is_dir():
                print('Uploading directory...')
            else:
                print('Uploading file...')

        result = uploader.upload(
            args.path,
            pin=not args.no_pin,
            wrap=args.wrap
        )

        cid = result['cid']

        if args.quiet:
            print(cid)
        else:
            print()
            print('\033[32mUpload successful!\033[0m')
            print('=' * 40)
            print(f'CID: \033[33m{cid}\033[0m')
            print(f'Size: {result["size"]} bytes')
            print()
            print('Access your content:')
            print(f'  Gateway: https://gateway.ubitquityx.com/ipfs/{cid}')
            print(f'  IPFS:    ipfs://{cid}')
            print()
            print('Verify pin status:')
            print(f'  constellation-cli pin ls {cid}')

    except FileNotFoundError as e:
        print(f'\033[31mError: {e}\033[0m', file=sys.stderr)
        sys.exit(1)

    except requests.exceptions.ConnectionError:
        print('\033[31mUpload failed!\033[0m', file=sys.stderr)
        print('Could not connect to the API endpoint.', file=sys.stderr)
        print()
        print('Troubleshooting:', file=sys.stderr)
        print('  1. Check if the API URL is correct', file=sys.stderr)
        print('  2. Verify the Constellation service is running', file=sys.stderr)
        print('  3. Check your network connection', file=sys.stderr)
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print('\033[31mUpload failed!\033[0m', file=sys.stderr)
        print(f'HTTP Error: {e}', file=sys.stderr)
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f'Details: {error_detail}', file=sys.stderr)
            except:
                print(f'Response: {e.response.text}', file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f'\033[31mUpload failed: {e}\033[0m', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
