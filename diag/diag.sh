# Disable conflicting services first
rc-update del crond default        # ❌ Remove crond
rc-update del crond boot           # ❌ Remove crond
rc-update del dnsmasq default      # ⚠️ Remove from Alpine's control
rc-update del dnsmasq boot         # ⚠️ Remove from Alpine's control

# Enable IPCop services
rc-update add fcron default        # ✅ Add fcron (replaces crond)
rc-update add dnsmasq default      # ✅ Re-add under IPCop control