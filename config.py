import os

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "biken-network-monitor-secret-2026")
    DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 8080))

    # Monitoring intervals (seconds)
    BANDWIDTH_INTERVAL   = 2    # how often to sample bandwidth
    PING_INTERVAL        = 5    # how often to ping hosts
    DEVICE_SCAN_INTERVAL = 30   # how often to scan for devices
    HISTORY_LENGTH       = 60   # number of datapoints to keep per metric

    # Ping targets
    PING_TARGETS = {
        "Google DNS":     "8.8.8.8",
        "Cloudflare DNS": "1.1.1.1",
        "OpenDNS":        "208.67.222.222",
    }

    # Alert thresholds
    ALERT_LATENCY_MS     = 150   # ms — warn if ping > this
    ALERT_PACKET_LOSS    = 20    # % — warn if packet loss > this
    ALERT_BANDWIDTH_MBPS = 90    # Mbps — warn if bandwidth > this
