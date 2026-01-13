#!/bin/sh
#
# ipcop-debug - Helper script to manage system call debug logging
#

SETTINGS_FILE="/var/ipcop/main/settings"
DEBUG_LOG="/var/log/ipcop/debug.log"

usage() {
    cat <<EOF
Usage: ipcop-debug {on|off|status|tail|clear}

Commands:
  on      Enable debug logging (requires restart of services)
  off     Disable debug logging
  status  Show current debug status
  tail    Tail the debug log in real-time
  clear   Clear the debug log
EOF
    exit 1
}

case "$1" in
    on)
        echo "Enabling debug logging..."
        sed -i 's/^DEBUG_SYSTEM_CALLS=.*/DEBUG_SYSTEM_CALLS=on/' "$SETTINGS_FILE"
        echo "✓ Debug logging enabled"
        echo "  Logs will be written to: $DEBUG_LOG"
        echo "  Note: Services may need restart to pick up changes"
        ;;
    
    off)
        echo "Disabling debug logging..."
        sed -i 's/^DEBUG_SYSTEM_CALLS=.*/DEBUG_SYSTEM_CALLS=off/' "$SETTINGS_FILE"
        echo "✓ Debug logging disabled"
        ;;
    
    status)
        if grep -q "^DEBUG_SYSTEM_CALLS=on" "$SETTINGS_FILE" 2>/dev/null; then
            echo "Debug logging: ENABLED"
            if [ -f "$DEBUG_LOG" ]; then
                SIZE=$(du -h "$DEBUG_LOG" | cut -f1)
                LINES=$(wc -l <"$DEBUG_LOG")
                echo "  Log file: $DEBUG_LOG ($SIZE, $LINES lines)"
            else
                echo "  Log file: not yet created"
            fi
        else
            echo "Debug logging: DISABLED"
        fi
        ;;
    
    tail)
        echo "Tailing debug log (Ctrl+C to exit)..."
        echo "----------------------------------------"
        tail -f "$DEBUG_LOG"
        ;;
    
    clear)
        if [ -f "$DEBUG_LOG" ]; then
            SIZE=$(du -h "$DEBUG_LOG" | cut -f1)
            rm -f "$DEBUG_LOG" "$DEBUG_LOG.old"
            echo "✓ Cleared debug log ($SIZE)"
        else
            echo "Debug log doesn't exist (nothing to clear)"
        fi
        ;;
    
    *)
        usage
        ;;
esac
