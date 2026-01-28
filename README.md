# IPFS Constellation

**The Enterprise Control Plane for Decentralized Storage**

Transform isolated IPFS nodes into a unified, resilient fleet. Constellation orchestrates your data pinset with military-grade redundancy and automated healing.

## Quick Start - Upload Now!

**Ready-to-use upload scripts are available in the [`scripts/`](scripts/) directory:**

```bash
# Bash
./scripts/upload.sh myfile.txt

# Node.js (requires: npm install ipfs-http-client)
node scripts/upload.js myfile.txt

# Python (requires: pip install requests)
python scripts/upload.py myfile.txt
```

Set your API endpoint:
```bash
export CONSTELLATION_API_URL="https://api.ubitquityx.com"
export CONSTELLATION_API_KEY="your-api-key"  # if required
```

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start---upload-now)
- [Node Uploading](#node-uploading)
  - [JavaScript/TypeScript](#javascripttypescript)
  - [Python](#python)
  - [cURL/CLI](#curlcli)
  - [Verifying Uploads](#verifying-uploads)
- [Server Requirements](#server-requirements)
  - [Minimum Hardware Specifications](#minimum-hardware-specifications)
  - [Storage Requirements](#storage-requirements)
  - [Network Requirements](#network-requirements)
- [Node Configuration](#node-configuration)
- [Firewall Configuration](#firewall-configuration)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

---

## Overview

IPFS Constellation provides:

- **99.9% Data Availability** through 3x replication across nodes
- **Zero Single Points of Failure** with leaderless CRDT consensus
- **Autonomic Self-Healing** with automatic pin retry and exponential backoff
- **Smart Fleet Balancing** with capacity and geo-aware routing
- **Hyperscale Ingestion** supporting hundreds of pins per second

---

## Node Uploading

IPFS Constellation exposes a **Proxy API** that mirrors standard IPFS HTTP API endpoints. This means you can use existing IPFS client libraries with zero code changes.

### Upload Endpoint

```
POST https://api.yourdomain.com/api/v0/add?pin=true
```

### JavaScript/TypeScript

Using `ipfs-http-client`:

```javascript
import { create } from 'ipfs-http-client'

// Basic connection
const ipfs = create({
  url: 'https://api.yourdomain.com'
})

// With authentication (recommended for production)
const ipfsAuth = create({
  url: 'https://api.yourdomain.com',
  headers: {
    authorization: 'Basic ' + Buffer.from(username + ':' + password).toString('base64')
  }
})

// Upload a file
async function uploadFile(content) {
  try {
    const { cid } = await ipfs.add(content, {
      pin: true  // Ensures content is pinned to the cluster
    })
    console.log('Data pinned to cluster:', cid.toString())
    return cid
  } catch (error) {
    console.error('Upload failed:', error.message)
    throw error
  }
}

// Upload from file path (Node.js)
async function uploadFromPath(filePath) {
  const fs = require('fs')
  const content = fs.readFileSync(filePath)
  return uploadFile(content)
}

// Example usage
uploadFile('Hello Constellation Fleet!')
```

### Python

Using `ipfshttpclient`:

```python
import ipfshttpclient

# Connect to your Constellation cluster
client = ipfshttpclient.connect('/dns/api.yourdomain.com/tcp/443/https')

# Upload a string
def upload_string(content):
    result = client.add_str(content)
    print(f"Data pinned to cluster: {result}")
    return result

# Upload a file
def upload_file(file_path):
    result = client.add(file_path, pin=True)
    print(f"File pinned to cluster: {result['Hash']}")
    return result['Hash']

# Example usage
cid = upload_string("Hello Constellation Fleet!")
print(f"CID: {cid}")
```

### cURL/CLI

For CI/CD pipelines and shell scripts:

```bash
# Upload a file
curl -X POST -F file=@myfile.txt \
  "https://api.yourdomain.com/api/v0/add?pin=true"

# Upload with authentication
curl -X POST -F file=@myfile.txt \
  -u "username:password" \
  "https://api.yourdomain.com/api/v0/add?pin=true"

# Upload a directory recursively
curl -X POST -F file=@mydir \
  "https://api.yourdomain.com/api/v0/add?pin=true&recursive=true"
```

### Verifying Uploads

After uploading, verify your content is replicated across the cluster:

```bash
# Check pin status across the cluster
constellation-cli pin ls <CID>

# Check replication status
constellation-cli status <CID>

# Retrieve content to verify
curl "https://gateway.yourdomain.com/ipfs/<CID>"
```

---

## Server Requirements

### Minimum Hardware Specifications

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 4 GB | 8 GB | 16+ GB |
| **Storage** | 100 GB SSD | 500 GB NVMe | 2+ TB NVMe |
| **Network** | 100 Mbps | 1 Gbps | 10 Gbps |

### Storage Requirements

**Base System:**
- Operating System: ~20 GB
- IPFS Daemon: ~500 MB
- Constellation Daemon: ~100 MB
- Logs and temp files: ~10 GB

**Data Storage (per node):**
- Minimum: 50 GB for pinned content
- Recommended: 500 GB - 2 TB depending on use case
- Plan for 3x replication factor (each file stored on 3 nodes minimum)

**Storage Calculation Formula:**
```
Total Storage Needed = (Expected Data Size) × (Replication Factor) / (Number of Nodes)
```

Example: For 1 TB of data with 3x replication across 5 nodes:
```
Storage per Node = (1 TB × 3) / 5 = 600 GB per node
```

### Network Requirements

**Bandwidth:**
- Minimum: 100 Mbps symmetric
- Recommended: 1 Gbps symmetric
- High-throughput: 10 Gbps

**Latency:**
- Inter-node latency: < 100ms recommended
- For geo-distributed clusters: < 300ms acceptable

**Required Ports:**

| Port | Protocol | Purpose | Public |
|------|----------|---------|--------|
| 22 | TCP | SSH Access | Yes (restricted) |
| 4001 | TCP/UDP | IPFS Swarm | Yes |
| 5001 | TCP | IPFS API | **NO - Internal Only** |
| 8080 | TCP | IPFS Gateway | Optional |
| 9096 | TCP | Constellation Swarm | Yes (cluster peers) |

---

## Node Configuration

### Minimum Cluster Size

- **Development:** 1 node (no redundancy)
- **Staging:** 2 nodes (limited redundancy)
- **Production:** 3+ nodes (quorum requirement for consensus)

### Configuration File

Location: `/etc/constellation/config.json`

```json
{
  "cluster": {
    "secret": "GENERATED_SECRET_HERE",
    "listen_multiaddress": "/ip4/0.0.0.0/tcp/9096",
    "replication_factor_min": 2,
    "replication_factor_max": 3
  },
  "ipfs_connector": {
    "api_multiaddress": "/ip4/127.0.0.1/tcp/5001"
  },
  "consensus": {
    "type": "crdt"
  }
}
```

### Deployment Commands

**Primary Node (generates cluster secret):**
```bash
sudo ./deploy.sh --role primary
```

**Worker Nodes (join existing cluster):**
```bash
sudo ./deploy.sh --role worker \
  --secret "YOUR_GENERATED_SECRET" \
  --bootstrap "/ip4/PRIMARY_IP/tcp/9096/p2p/PEER_ID"
```

---

## Firewall Configuration

```bash
# Allow SSH (restrict to your IP)
ufw allow from YOUR_IP to any port 22 proto tcp

# Allow IPFS Swarm
ufw allow 4001/tcp
ufw allow 4001/udp

# Allow Constellation Swarm
ufw allow 9096/tcp

# Allow IPFS Gateway (optional, for public access)
ufw allow 8080/tcp

# IMPORTANT: Do NOT expose port 5001 (IPFS API)
# ufw deny 5001/tcp  # Should be blocked by default

# Enable firewall
ufw enable
```

---

## Troubleshooting

### Upload Fails with Connection Error

1. **Check IPFS daemon is running:**
   ```bash
   systemctl status ipfs
   ```

2. **Verify Constellation service:**
   ```bash
   systemctl status constellation
   ```

3. **Check API endpoint accessibility:**
   ```bash
   curl -v https://api.yourdomain.com/api/v0/id
   ```

### Upload Succeeds but Content Not Replicated

1. **Check cluster peer status:**
   ```bash
   constellation-cli peers ls
   ```

2. **Verify replication settings in config:**
   ```bash
   cat /etc/constellation/config.json | grep replication
   ```

3. **Check available storage on peers:**
   ```bash
   constellation-cli peers ls --storage
   ```

### Slow Upload Speeds

1. **Check network connectivity between nodes:**
   ```bash
   ping -c 5 PEER_IP
   ```

2. **Verify no bandwidth throttling:**
   ```bash
   iperf3 -c PEER_IP
   ```

3. **Check disk I/O:**
   ```bash
   iostat -x 1 5
   ```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `connection refused` | IPFS/Constellation not running | Start services: `systemctl start ipfs constellation` |
| `unauthorized` | Invalid or missing credentials | Check API key/password configuration |
| `no space left` | Disk full | Add storage or remove old pins |
| `peer not found` | Cluster connectivity issue | Check firewall and network settings |

---

## Resources

### Documentation

- [Developer Integration Guide](docs/IPFS_Constellation_Developer_Integration_Guide.pdf)
- [Deployment Guide](docs/IPFS_Constellation_Deployment_Guide.pdf)
- [Whitepaper](whitepaper/IPFS_Constellation_Whitepaper_v_1_0.pdf)
- [Monetization Strategy & Pricing](MONETIZATION_STRATEGY.md)

### Upload Scripts

Ready-to-use scripts for uploading content:

- [Bash Script](scripts/upload.sh) - For shell/CI/CD pipelines
- [Node.js Script](scripts/upload.js) - For JavaScript environments
- [Python Script](scripts/upload.py) - For Python environments

### Live Public Nodes

- Primary Gateway: [ubitquityx.com](https://ubitquityx.com)
- Secondary Gateway: [smartescrow.us](https://smartescrow.us)

### Support

- Portal: [ubitquityx.com/IPFS_Constellation](https://ubitquityx.com/IPFS_Constellation)
- Support: [support.ubitquityx.com](https://support.ubitquityx.com)
- GitHub: [github.com/ubitquity/IPFS-CONSTELLATION_PUBLIC](https://github.com/ubitquity/IPFS-CONSTELLATION_PUBLIC)

---

## License

See [LICENSE](LICENSE) for details.
