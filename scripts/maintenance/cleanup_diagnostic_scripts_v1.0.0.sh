#!/bin/bash
# Cleanup all diagnostic PHP scripts from live server

SSH_USER="git_deployer_32064108a7_545525"
SSH_HOST="bp6.0cf.myftpupload.com"

echo "Removing diagnostic scripts from GoDaddy server..."

ssh ${SSH_USER}@${SSH_HOST} "cd html && rm -f \
  update-homepage.php \
  UPDATED_HOMEPAGE_LOUISVILLE_COLORS.html \
  wp-rest-api-diagnostic.php \
  fix-rest-api-permissions.php \
  fix-user-role.php \
  check-database-user.php \
  check-mu-plugins.php \
  list-all-users.php \
  deactivate-jetpack.php \
  check-configs-file.php \
  check-all-users-raw.php \
  show-db-error.php \
  check-users-wp.php \
  test-user-caps.php \
  fix-role-properly.php \
  check-roles-defined.php \
  restore-wordpress-roles.php"

echo "✅ Cleanup complete!"
echo ""
echo "Remaining files on server:"
ssh ${SSH_USER}@${SSH_HOST} "cd html && ls -la *.php | grep -v wp-"
