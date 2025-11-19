#!/bin/bash
# Test: Verify all development tools exist

source "$(dirname $0)/../test_helpers.sh"

test_skippy_profile_exists() {
    assert_file_exists "/home/dave/skippy/bin/skippy-profile"
}

test_health_dashboard_exists() {
    assert_file_exists "/home/dave/skippy/bin/health-dashboard"
}

test_skippy_script_exists() {
    assert_file_exists "/home/dave/skippy/bin/skippy-script"
}

test_tools_executable() {
    assert_command_succeeds "test -x /home/dave/skippy/bin/skippy-profile"
    assert_command_succeeds "test -x /home/dave/skippy/bin/health-dashboard"
    assert_command_succeeds "test -x /home/dave/skippy/bin/skippy-script"
}

# Run tests
run_test "skippy-profile exists" test_skippy_profile_exists
run_test "health-dashboard exists" test_health_dashboard_exists
run_test "skippy-script exists" test_skippy_script_exists
run_test "tools are executable" test_tools_executable

test_summary
