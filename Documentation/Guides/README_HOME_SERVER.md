# Home Server Master Controller

A unified management system that integrates all your server components into a single, easy-to-manage platform.

## Features

- **Unified Management**: Single control point for all server components
- **Component Integration**: 
  - System cleanup and maintenance (TidyTux)
  - Ethereum node management
  - Cloud synchronization (Google Drive)
  - AI-powered maintenance
  - Multi-server support
- **Health Monitoring**: Real-time component status and system metrics
- **Web Interface**: Optional web UI for remote management
- **Service Management**: Automatic startup with systemd
- **Event System**: Component communication and automation
- **Modular Design**: Enable/disable components as needed

## Quick Start

1. **Install**: Run the installer script
   ```bash
   chmod +x home_server_installer.sh
   ./home_server_installer.sh
   ```

2. **Configure**: Edit `~/.home-server/config/server.yaml` to enable/disable components

3. **Start**: Launch the server
   ```bash
   home-server start
   ```

4. **Check Status**: View component health
   ```bash
   home-server status
   ```

## Configuration

The main configuration file is located at `~/.home-server/config/server.yaml`:

```yaml
# Enable/disable components
enable_system_manager: true
enable_ethereum_node: false
enable_cloud_sync: true
enable_monitoring: true
enable_ai_maintenance: false

# Server settings
server_port: 8080
enable_web_ui: true
```

## Command Line Usage

```bash
# Start the server
home-server start

# Check status
home-server status

# Configure settings
home-server configure --enable-ethereum --port 8080

# View help
home-server --help
```

## Systemd Service

Enable automatic startup:
```bash
systemctl --user enable home-server.service
systemctl --user start home-server.service
```

Check service status:
```bash
systemctl --user status home-server.service
```

## Web Interface

When enabled, access the web UI at: http://localhost:8080

## Directory Structure

```
~/.home-server/
├── config/          # Configuration files
├── logs/            # Log files
├── data/            # Application data
├── components/      # Component scripts
├── plugins/         # Custom plugins
└── backups/         # Backup files
```

## Components

### System Manager
Handles system cleanup, package management, and maintenance tasks.

### Ethereum Node
Manages Ethereum node setup and operation (requires enabling in config).

### Cloud Sync
Synchronizes files with Google Drive using rclone.

### Monitoring
Tracks system health, resource usage, and component status.

### AI Maintenance
Provides intelligent maintenance recommendations (requires API key).

## Troubleshooting

Check logs: `~/.home-server/logs/`

Common issues:
- Port already in use: Change `server_port` in config
- Component not starting: Check component-specific logs
- Permission denied: Ensure proper file permissions

## Security

- Runs as non-root user
- Component isolation
- Configurable access controls
- Audit logging

## Requirements

- Linux system
- Python 3.6+
- systemd (optional, for service management)
- Component-specific requirements (see individual components)