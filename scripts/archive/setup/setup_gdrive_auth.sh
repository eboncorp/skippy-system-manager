#!/bin/bash

# The authorization token from the remote authorization
AUTH_TOKEN='eyJ0b2tlbiI6IntcImFjY2Vzc190b2tlblwiOlwieWEyOS5hMEFRUV9CRFJiXzRaSzItbVJZSTh2LW9aWGRoOUQ1MGZaWFhBTlMzNF9TSThWU0drYmFyNW0wMjNlOEhqWkRiNmZBRnJudXYyRjhQWHdsdFVOSVRSVnhDN3RoeW1fRkpZRmV3eEt5OGJTV2U4R3diTW1nMGZxa2g3Nm1KTjVGWVFMWXU5ejUxbFdpdkNTbVFKZnI0bWtVelpqWUQwWGQwSzJtUjRlSkE5TklaSWFKd3MxZlUtWml3WjlxUXdSYWQtRW5UOUZzWjBhQ2dZS0FRb1NBUlVTRlFIR1gyTWlGTnM4S2hTaUdMWWVtNmFUMHNiZGlnMDIwNlwiLFwidG9rZW5fdHlwZVwiOlwiQmVhcmVyXCIsXCJyZWZyZXNoX3Rva2VuXCI6XCIxLy8wMTBXZE53aXlfcUpvQ2dZSUFSQUFHQUVTTndGLUw5SXJPNkNRVjNhQXVpNjZSWmx3NVJDMDY3R3VtV1NpMnFjNGNiRjRwNEpwM2hVOUxsMWlmY1VSOFFhU0JKWmFPWTVkVFB3XCIsXCJleHBpcnlcIjpcIjIwMjUtMDktMjhUMTY6NTA6MzguNTMyMzczNjk1LTA0OjAwXCIsXCJleHBpcmVzX2luXCI6MzU5OX0ifQ'

echo "Updating Google Drive configuration with new authorization..."

# Use expect to automate the interactive configuration
expect << EOF
spawn rclone config

# Wait for the menu
expect "e/n/d/r/c/s/q>"
send "e\r"

# Select googledrive remote
expect "Choose a number from below"
send "1\r"

# Edit remote menu - choose to edit the configuration
expect "Edit remote"
expect "Value"
send "n\r"

# When asked for client_id, just press enter to keep existing
expect "client_id>"
send "\r"

# When asked for client_secret, just press enter to keep existing
expect "client_secret>"
send "\r"

# When asked for scope, keep existing
expect "scope>"
send "\r"

# When asked for service_account_file, keep existing
expect "service_account_file>"
send "\r"

# When asked for token, paste the new one
expect "Enter verification code>"
send "$AUTH_TOKEN\r"

# Confirm the configuration
expect "y/n>"
send "y\r"

# Back to main menu
expect "e/n/d/r/c/s/q>"
send "q\r"

expect eof
EOF

echo "Configuration updated. Testing connection..."
rclone lsd googledrive: