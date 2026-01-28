#!/usr/bin/env node
/**
 * IPFS Constellation Upload Script (Node.js)
 *
 * Upload files to your Constellation cluster
 *
 * Installation:
 *   npm install ipfs-http-client
 *
 * Usage:
 *   node upload.js <file_path>
 *   node upload.js --url https://api.example.com myfile.txt
 *
 * Environment variables:
 *   CONSTELLATION_API_URL - API endpoint
 *   CONSTELLATION_API_KEY - API key for authentication
 */

const fs = require('fs');
const path = require('path');

// Check for ipfs-http-client
let create;
try {
    create = require('ipfs-http-client').create;
} catch (e) {
    console.error('Error: ipfs-http-client not installed');
    console.error('Run: npm install ipfs-http-client');
    process.exit(1);
}

// Configuration
const config = {
    apiUrl: process.env.CONSTELLATION_API_URL || 'https://api.ubitquityx.com',
    apiKey: process.env.CONSTELLATION_API_KEY || '',
    username: process.env.CONSTELLATION_USERNAME || '',
    password: process.env.CONSTELLATION_PASSWORD || ''
};

// Parse command line arguments
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        url: config.apiUrl,
        key: config.apiKey,
        pin: true,
        wrap: false,
        quiet: false,
        files: []
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '-u':
            case '--url':
                options.url = args[++i];
                break;
            case '-k':
            case '--key':
                options.key = args[++i];
                break;
            case '-w':
            case '--wrap':
                options.wrap = true;
                break;
            case '--no-pin':
                options.pin = false;
                break;
            case '-q':
            case '--quiet':
                options.quiet = true;
                break;
            case '-h':
            case '--help':
                printUsage();
                process.exit(0);
            default:
                if (!args[i].startsWith('-')) {
                    options.files.push(args[i]);
                }
        }
    }

    return options;
}

function printUsage() {
    console.log(`
IPFS Constellation Upload Script (Node.js)

Usage: node upload.js [OPTIONS] <file_or_directory>

Options:
  -u, --url URL       API endpoint URL
  -k, --key KEY       API key for authentication
  -w, --wrap          Wrap files in a directory
  --no-pin            Don't pin after upload
  -q, --quiet         Suppress output except CID
  -h, --help          Show this help message

Environment Variables:
  CONSTELLATION_API_URL    - API endpoint
  CONSTELLATION_API_KEY    - API key
  CONSTELLATION_USERNAME   - Basic auth username
  CONSTELLATION_PASSWORD   - Basic auth password

Examples:
  node upload.js myfile.txt
  node upload.js --url https://api.example.com ./my-folder/
  CONSTELLATION_API_KEY=xxx node upload.js document.pdf
`);
}

// Create IPFS client
function createClient(options) {
    const clientOptions = {
        url: options.url
    };

    // Add authentication if provided
    if (options.key) {
        clientOptions.headers = {
            authorization: `Bearer ${options.key}`
        };
    } else if (config.username && config.password) {
        const auth = Buffer.from(`${config.username}:${config.password}`).toString('base64');
        clientOptions.headers = {
            authorization: `Basic ${auth}`
        };
    }

    return create(clientOptions);
}

// Get all files from a directory recursively
async function* getFiles(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);

        if (entry.isDirectory()) {
            yield* getFiles(fullPath);
        } else {
            yield {
                path: fullPath,
                content: fs.readFileSync(fullPath)
            };
        }
    }
}

// Upload a single file
async function uploadFile(ipfs, filePath, options) {
    const content = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);

    const result = await ipfs.add({
        path: fileName,
        content: content
    }, {
        pin: options.pin,
        wrapWithDirectory: options.wrap
    });

    return result;
}

// Upload a directory
async function uploadDirectory(ipfs, dirPath, options) {
    const files = [];
    const baseName = path.basename(dirPath);

    for await (const file of getFiles(dirPath)) {
        const relativePath = path.relative(dirPath, file.path);
        files.push({
            path: path.join(baseName, relativePath),
            content: file.content
        });
    }

    let lastResult;
    for await (const result of ipfs.addAll(files, {
        pin: options.pin,
        wrapWithDirectory: options.wrap
    })) {
        lastResult = result;
    }

    return lastResult;
}

// Main function
async function main() {
    const options = parseArgs();

    if (options.files.length === 0) {
        console.error('Error: No file or directory specified');
        printUsage();
        process.exit(1);
    }

    const filePath = options.files[0];

    if (!fs.existsSync(filePath)) {
        console.error(`Error: File or directory not found: ${filePath}`);
        process.exit(1);
    }

    if (!options.quiet) {
        console.log('IPFS Constellation Upload');
        console.log('========================');
        console.log(`API URL: ${options.url}`);
        console.log(`File: ${filePath}`);
        console.log(`Pin: ${options.pin}`);
        console.log('');
    }

    try {
        const ipfs = createClient(options);
        let result;

        const stats = fs.statSync(filePath);

        if (stats.isDirectory()) {
            if (!options.quiet) {
                console.log('Uploading directory...');
            }
            result = await uploadDirectory(ipfs, filePath, options);
        } else {
            if (!options.quiet) {
                console.log('Uploading file...');
            }
            result = await uploadFile(ipfs, filePath, options);
        }

        const cid = result.cid.toString();

        if (options.quiet) {
            console.log(cid);
        } else {
            console.log('');
            console.log('\x1b[32mUpload successful!\x1b[0m');
            console.log('================================');
            console.log(`CID: \x1b[33m${cid}\x1b[0m`);
            console.log(`Size: ${result.size} bytes`);
            console.log('');
            console.log('Access your content:');
            console.log(`  Gateway: https://gateway.ubitquityx.com/ipfs/${cid}`);
            console.log(`  IPFS:    ipfs://${cid}`);
            console.log('');
            console.log('Verify pin status:');
            console.log(`  constellation-cli pin ls ${cid}`);
        }

    } catch (error) {
        console.error('');
        console.error('\x1b[31mUpload failed!\x1b[0m');
        console.error(`Error: ${error.message}`);

        if (error.message.includes('ECONNREFUSED')) {
            console.error('');
            console.error('Troubleshooting:');
            console.error('  1. Check if the API URL is correct');
            console.error('  2. Verify the Constellation service is running');
            console.error('  3. Check your network connection');
        }

        process.exit(1);
    }
}

main();
