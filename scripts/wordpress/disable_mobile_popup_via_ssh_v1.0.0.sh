#!/bin/bash
# Run this via SSH to disable the mobile popup directly in database

echo "Disabling Astra Mobile Popup via SSH..."

# SSH into GoDaddy and run WP-CLI command
ssh git_deployer_2d3dd1104a_545525@bp6.0cf.myftpupload.com << 'ENDSSH'
cd html
wp option patch update astra-settings mobile-popup-drawer ''
wp option patch update astra-settings mobile-header-type 'dropdown'
wp cache flush
echo "Mobile popup disabled!"
ENDSSH

echo "Done! Now clear Cloudflare cache."
