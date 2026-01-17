# TODO List - IPCop-Alpine

## Suricata Issues

### --af-packet Flag Investigation
- [ ] Investigate why `--af-packet` flag doesn't appear in running Suricata process despite being added to `/source/services/suricata/etc/init.d/suricata`
- [ ] Verify the init script is properly installed to the system
- [ ] Check if the flag is being passed correctly in the start command
- [ ] Test Suricata startup manually with the flag to confirm it works
- [ ] Review Suricata logs for any related errors or warnings

## Service Management

### General Service Start/Stop Behavior
- [ ] Implement service enablement checks - services should only start if enabled in IPCop configuration
- [ ] Ensure enabled services start automatically on boot
- [ ] Ensure enabled services remain running between reboots
- [ ] Prevent disabled services from starting to avoid interference
- [ ] Reduce resource requirements by not running unnecessary services
- [ ] Review and standardize init scripts across all services
- [ ] Add IPCop configuration checks to each service's init script
- [ ] Test service persistence across reboots

## Testing Infrastructure

### Environment Testing Framework
- [ ] Create testing directory structure following package organization:
  - Core firewall tests in `core/` package area
  - Squid proxy tests in `squid/` package area  
  - e2guardian URL filter tests in `e2guardian/` package area
- [ ] Implement environment validation tests (similar to `install.sh` checks)
  - System requirements validation
  - Architecture detection
  - Dependency verification
  - File system structure validation
- [ ] Implement firewall behavior tests
  - Rule application verification
  - Network interface configuration
  - Traffic filtering validation
- [ ] Implement service behavior tests per package
  - Service start/stop functionality
  - Configuration file generation
  - Log file creation and permissions
  - Process persistence

---
*Last updated: 2026-01-17*
