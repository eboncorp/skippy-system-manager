"title": "Ethereum Node Overview",
    "tags": ["ethereum"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 0,
    "refresh": "5s",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[1m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "100 * (1 - ((node_memory_MemAvailable_bytes{} or node_memory_MemFree_bytes{} + node_memory_Buffers_bytes{} + node_memory_Cached_bytes{}) / node_memory_MemTotal_bytes{}))",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "100 - ((node_filesystem_avail_bytes{mountpoint=\"/\"} * 100) / node_filesystem_size_bytes{mountpoint=\"/\"})",
            "legendFormat": "{{instance}}"
          }
        ]
      }
    ]
  },
  "overwrite": false
}
EOF
)

    # Use Grafana API to create dashboard
    curl -X POST -H "Content-Type: application/json" -d "$dashboard_json" http://admin:admin@localhost:3000/api/dashboards/db
    
    log_info "Grafana dashboard created successfully."
}

# Run benchmark
run_benchmark() {
    log_info "Running performance benchmark..."

    # CPU benchmark
    log_info "Running CPU benchmark..."
    sysbench cpu --cpu-max-prime=20000 run > /tmp/cpu_benchmark.log

    # Memory benchmark
    log_info "Running memory benchmark..."
    sysbench memory --memory-total-size=10G run > /tmp/memory_benchmark.log

    # Disk I/O benchmark
    log_info "Running disk I/O benchmark..."
    sysbench fileio --file-total-size=10G prepare
    sysbench fileio --file-total-size=10G --file-test-mode=rndrw run > /tmp/disk_benchmark.log
    sysbench fileio --file-total-size=10G cleanup

    # Network benchmark
    log_info "Running network benchmark..."
    iperf3 -c iperf.he.net > /tmp/network_benchmark.log

    log_info "Benchmark completed. Results saved in /tmp/*_benchmark.log"
}

# Setup validator (if enabled)
setup_validator() {
    log_info "Setting up validator..."

    if [ "$DRY_RUN" = false ]; then
        # Generate or import validator keys
        if [ ! -d "$VALIDATOR_KEYS_DIR" ]; then
            mkdir -p "$VALIDATOR_KEYS_DIR"
            # Here you would typically run the key generation tool for your chosen client
            # For example, for Prysm:
            # prysm.sh validator accounts create --wallet-dir=$VALIDATOR_KEYS_DIR
        else
            log_info "Validator keys directory already exists. Skipping key generation."
        fi

        # Set up validator service
        cat > /etc/systemd/system/ethereum-validator.service << EOF
[Unit]
Description=Ethereum Validator
After=ethereum-consensus.service
Wants=ethereum-consensus.service

[Service]
User=$ETH_USER
ExecStart=/usr/local/bin/validator-client --datadir $VALIDATOR_KEYS_DIR
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable ethereum-validator
        systemctl start ethereum-validator

        log_info "Validator setup completed."
    else
        log_info "Dry run: Would set up validator"
    fi
}

# Setup MEV-Boost (if enabled)
setup_mev_boost() {
    log_info "Setting up MEV-Boost..."

    if [ "$DRY_RUN" = false ]; then
        # Install MEV-Boost
        wget https://github.com/flashbots/mev-boost/releases/download/v1.5.0/mev-boost_1.5.0_amd64.deb
        dpkg -i mev-boost_1.5.0_amd64.deb

        # Set up MEV-Boost service
        cat > /etc/systemd/system/mev-boost.service << EOF
[Unit]
Description=MEV-Boost Relay
After=network-online.target
Wants=network-online.target

[Service]
User=$ETH_USER
ExecStart=/usr/local/bin/mev-boost -mainnet -relay-check -relays https://0x8b5d2e73e2a3a55c6c87b8b6eb92e0149a125c852751db1422fa951e42a09b82c142c3ea98d0d9930b056a3bc9896b8f@bloxroute.max-profit.blxrbdn.com
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable mev-boost
        systemctl start mev-boost

        log_info "MEV-Boost setup completed."
    else
        log_info "Dry run: Would set up MEV-Boost"
    fi
}

# Main execution
if [ "$UNINSTALL" = true ]; then
    uninstall_ethereum_node
elif [ "$UPDATE" = true ]; then
    if [ "$AUTO_UPDATE_ENABLED" = true ]; then
        automated_update
    else
        check_for_script_update
    fi
elif [ "$BENCHMARK" = true ]; then
    run_benchmark
else
    main
fi

log_info "Ethereum node setup script completed. Please review the logs for any warnings or errors."
