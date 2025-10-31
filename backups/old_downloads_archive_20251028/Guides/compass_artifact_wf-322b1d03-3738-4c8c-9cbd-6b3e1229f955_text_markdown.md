# Multi-Service Blockchain and Media Server Configuration Guide

Running a media server alongside Ethereum and Chainlink nodes on a single system represents a complex but achievable configuration that can provide both entertainment services and potential blockchain revenue streams. Based on current 2024/2025 requirements, the **Gigabyte R113-C10-AA01-L1 server with AMD EPYC 4464P processor offers superior efficiency and cost-effectiveness** compared to upgrading the existing HP Z4 G4, delivering 23% lower power consumption and $741 in initial cost savings while providing modern DDR5 memory support and professional 1U rackmount design.

The convergence of blockchain infrastructure with media services demands careful resource orchestration. Current Ethereum blockchain storage exceeds 3TB and grows at approximately 750GB annually, while Chainlink nodes require dedicated database resources and low-latency network connectivity. Combined with 4K media transcoding demands, these services necessitate a minimum of 64GB RAM, though **128GB DDR5 ECC memory is strongly recommended** for stable multi-service operation. The total three-year cost of ownership for either hardware path approaches $8,310, with potential Chainlink node revenue offering break-even within 6 months to 2 years depending on operator status and network activity.

## 1. Hardware requirements analysis reveals critical specifications

The simultaneous operation of these three services imposes substantial hardware demands that exceed typical consumer-grade systems. CPU requirements alone demonstrate the need for enterprise-grade components, with media server 4K HDR transcoding requiring 17,000 PassMark score per stream, Ethereum full nodes demanding 8-12 cores with single-thread PassMark scores exceeding 3,500, and production Chainlink nodes needing 4 dedicated cores plus additional resources for PostgreSQL database operations.

Memory allocation proves equally critical with distinct requirements for each service. The Ethereum full node requires **32-64GB RAM for stable operation**, particularly during periods of high network activity or when processing complex smart contracts. Chainlink nodes demand 8-16GB for the node itself plus an additional 16GB for the PostgreSQL database when handling more than 100 jobs. Media servers require 16-32GB depending on transcoding load and library size, with additional overhead needed for the operating system and containerization layer.

Storage requirements have evolved dramatically with blockchain growth. The Ethereum blockchain currently exceeds 3TB in size, growing at approximately 14GB weekly or 750GB annually, with projections suggesting 8-10TB by 2027. **High-performance NVMe SSDs with minimum 7GB/s read speeds and 1 million IOPS for 4K random operations are mandatory** - traditional hard drives cannot sustain the required throughput for blockchain synchronization. Media libraries require separate storage, typically 10-20TB for substantial collections, though these can utilize traditional SATA drives or hybrid storage solutions.

## 2. Hardware comparison favors modern EPYC architecture

The AMD EPYC 4464P processor in the Gigabyte R113-C10-AA01-L1 server delivers exceptional performance-per-watt with its 12-core/24-thread Zen 4 architecture operating at 3.7GHz base and 5.4GHz boost frequencies. With only 65W TDP compared to 140-165W for comparable Intel Xeon processors, the EPYC platform reduces both operational costs and cooling requirements while maintaining PassMark scores exceeding 47,000 for multi-threaded workloads.

The comparison between platforms reveals distinct advantages for the Gigabyte solution despite some limitations. While the HP Z4 G4 offers superior expansion capabilities with five PCIe 3.0 slots and support for up to 512GB DDR4 memory, the Gigabyte server's **DDR5-5200 ECC support provides 66% higher memory bandwidth** crucial for blockchain operations. The compact 1U form factor limits expansion but suits professional deployment scenarios better than desktop towers.

Optimal storage configuration combines an **8TB PCIe 5.0 NVMe SSD for blockchain data** (Samsung 990 Pro or WD Black SN850X at approximately $599-649) with a 20TB enterprise HDD for media storage (Seagate Exos X20 at $349). Network requirements are satisfied by the built-in dual 1GbE Intel I210-AT controllers, though a 10GbE upgrade card adds only $200 for future bandwidth needs. Essential supporting infrastructure includes a 1500VA UPS system ($189-329) providing 15-30 minutes runtime for graceful shutdown during power failures.

## 3. Software stack leverages containerization for service isolation

Ubuntu Server 24.04 LTS emerges as the optimal operating system choice, offering five-year support lifecycle, extensive community documentation, and native support for all required blockchain clients. Docker with Docker Compose provides the ideal containerization strategy, balancing simplicity with powerful orchestration capabilities while maintaining strong service isolation and enabling easy backup and migration procedures.

For media serving, **Jellyfin surpasses both Plex and Emby** through its completely open-source model with all features available without subscription, including hardware transcoding support. The absence of licensing fees becomes particularly relevant when Plex lifetime passes increase from $120 to $249.99 in April 2025. Jellyfin's latest 10.9.x release offers comparable functionality with moderate resource consumption and extensive customization options.

Ethereum client selection favors **Nethermind for its fast synchronization times under 24 hours** and reliable operation with good resource efficiency. The latest 1.25.x releases demonstrate superior storage efficiency compared to Geth, though Geth remains viable for maximum compatibility given its 80% market share. Chainlink node software version 2.26.0+ requires PostgreSQL 12+ and benefits from SSL-secured connections to the Ethereum client, with production deployments demanding careful attention to database optimization and connection pooling.

## 4. System architecture prioritizes bare metal with containerization

The recommended architecture deploys services directly on bare metal with Docker containerization, eliminating virtualization overhead while maintaining service isolation. This approach maximizes performance for blockchain nodes requiring high I/O throughput while simplifying management through Docker Compose orchestration. Resource allocation dedicates 60% of CPU resources to blockchain services, 30% to media transcoding, and 10% for system overhead.

Storage layout employs EXT4 filesystems for reliability with blockchain workloads, avoiding the complexity of ZFS or the relative immaturity of BTRFS. The partition scheme allocates the 8TB NVMe entirely to `/opt/blockchain` for Ethereum and Chainlink data, while media storage resides on separate drives mounted at `/media/storage`. **System memory swappiness should be set to 10** to minimize swap usage while maintaining stability under memory pressure.

Network configuration implements VLANs for traffic segregation with management, blockchain P2P, and media streaming traffic isolated on separate virtual networks. UFW firewall rules restrict access to essential ports only: 30303 for Ethereum P2P, 6688 for Chainlink (internal only), and 8096 for Jellyfin streaming. Nginx reverse proxy handles SSL termination and provides additional security through rate limiting and header manipulation.

## 5. Performance optimization employs multi-layered strategies

CPU optimization through process priority management assigns nice values of -5 for Ethereum, 0 for Chainlink, and 5 for media services, ensuring blockchain operations receive priority during resource contention. CPU affinity dedicates cores 0-7 for blockchain services and 8-15 for media transcoding, preventing cache thrashing and context switching overhead. Cgroups enforce hard limits with 60% CPU allocation to blockchain services, 30% to media serving, and 10% reserved for system operations.

Memory optimization enables 2MB huge pages for database operations, significantly improving TLB hit rates for blockchain state access. **Memory limits prevent runaway processes from destabilizing the system**, with Ethereum capped at 64GB, Chainlink at 32GB including PostgreSQL, and media services at 32GB. The `/dev/shm` RAM disk accelerates media transcoding by eliminating disk I/O for temporary files.

Storage I/O optimization configures queue depths of 32-64 for blockchain operations and 16 for media transcoding, with the `mq-deadline` scheduler providing optimal performance for NVMe SSDs. Network traffic shaping through `tc` implements quality of service policies prioritizing blockchain traffic during synchronization while ensuring media streams maintain consistent bandwidth. Thermal management maintains CPU temperatures below 70°C and SSD temperatures below 60°C through aggressive fan curves and proper airflow design.

## 6. Cost analysis reveals competitive ROI potential

Hardware costs for the complete Gigabyte R113-C10-AA01-L1 system total $3,325 including server chassis with EPYC 4464P ($899), 128GB DDR5 ECC memory ($1,000), 8TB NVMe SSD ($599), 20TB enterprise HDD ($349), and essential peripherals. The HP Z4 G4 upgrade path costs $2,230-3,250 but requires existing hardware and delivers lower performance per watt.

Operating expenses vary significantly by region with annual electricity costs ranging from $243-561 for efficient EPYC systems to $486-1,123 for higher-consumption Intel platforms. **At the national average of $0.1387/kWh, annual power costs approximate $486 for 400W average consumption**. Business-grade gigabit internet adds $960-1,800 annually, while cooling costs multiply base power consumption by 1.2-1.5x.

Chainlink node revenue projections span wide ranges depending on operator status. Community nodes generate $500-1,500 monthly with break-even in 6 months to 2 years, while official node operators report average annual net income of $628,000 though selection remains highly competitive. Conservative projections suggest $1,200-13,200 annual profit after expenses, providing reasonable ROI for the initial hardware investment.

## 7. Implementation follows phased deployment strategy

The implementation plan spans four weeks with clearly defined phases ensuring systematic deployment and validation. Week one focuses on infrastructure setup including OS installation, storage configuration, and Docker deployment. **Ethereum node synchronization begins in week two**, requiring 2-3 days for initial sync using checkpoint synchronization to accelerate the process. Chainlink node deployment follows Ethereum synchronization, as the oracle service depends on blockchain connectivity.

Migration from the existing HP Z4 G4 media server utilizes rsync for data transfer, preserving directory structures and permissions while enabling incremental updates. Watch history and user preferences migrate through specialized tools like Plex2Jellyfin for automated conversion between platforms. The JellyPlex-Watched container enables bidirectional synchronization during the transition period, allowing gradual user migration without service disruption.

Testing procedures encompass performance benchmarking, stress testing, and failover validation. Ethereum RPC endpoints undergo latency testing while media transcoding capabilities face multi-stream load tests. System stress testing with tools like stress-ng and fio validates hardware stability under maximum load conditions. **Failover testing confirms service recovery** after simulated failures including network interruptions, storage disconnections, and power failures.

## 8. Monitoring strategy enables proactive maintenance

Comprehensive monitoring through Prometheus, Grafana, and Netdata provides real-time visibility into all service metrics. Custom Grafana dashboards display Ethereum sync progress, Chainlink job execution rates, media streaming statistics, and system resource utilization on unified displays. Alert thresholds trigger notifications for critical events including blockchain desynchronization, high resource usage exceeding 80%, and backup failures.

Automated backup strategies implement the 3-2-1 rule with local backups to separate drives, network backups to NAS systems, and cloud backups to S3-compatible storage. **Critical data including blockchain keys and configurations receive daily backups**, while full system backups occur weekly. Database dumps execute every six hours to minimize potential data loss. LVM snapshots enable consistent backups without service interruption.

Maintenance procedures balance automation with manual oversight. Security updates apply automatically for non-critical packages while blockchain client updates require manual testing on testnets before production deployment. Scheduled maintenance windows on Sunday mornings from 2:00-6:00 AM minimize user impact while providing regular opportunities for system optimization and hardware health checks.

The convergence of blockchain infrastructure with media services on a single high-performance system represents an ambitious but achievable configuration. With proper hardware selection, careful resource allocation, and comprehensive monitoring, this setup delivers both entertainment services and blockchain revenue potential while maintaining operational efficiency and reliability. The recommended Gigabyte R113-C10-AA01-L1 platform with AMD EPYC 4464P processor provides the optimal foundation for this demanding multi-service deployment, offering superior performance per watt and modern architecture advantages that position the system for sustained operation through 2027 and beyond.