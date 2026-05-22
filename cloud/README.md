# ThreatSense Cloud Server

Run this Flask server on the AWS EC2 VM:

```bash
python cloud/server.py
```

Cloud URLs:

- Dashboard: `http://52.53.150.132:5001`
- Health check: `http://52.53.150.132:5001/health`
- Alerts API: `http://52.53.150.132:5001/alerts`
- Alert receiver: `http://52.53.150.132:5001/cloud-alert`

The EC2 security group must allow inbound TCP traffic on port `5001`.
