#!/bin/bash
# MCP Control - enable/disable MCP servers
# Usage: ./mcp.sh on kaggle    # enable kaggle
#        ./mcp.sh off kaggle   # disable kaggle
#        ./mcp.sh on colab     # enable colab
#        ./mcp.sh status       # show all status

CONFIG="$HOME/.pi/agent/mcp-servers.json"
EXT="$HOME/.pi/agent/extensions/pi-mcp-host.ts"

case "$1" in
  on|off)
    if [ "$1" = "on" ]; then
      # Enable MCP host
      [ -f "${EXT}.disabled" ] && mv "${EXT}.disabled" "$EXT"
      # Enable specific server
      python3 -c "
import json
d = json.load(open('$CONFIG'))
d['mcpServers']['$2']['disabled'] = False
json.dump(d, open('$CONFIG','w'), indent=2)
print(f'✅ $2 enabled')
"
    else
      # Disable specific server
      python3 -c "
import json
d = json.load(open('$CONFIG'))
d['mcpServers']['$2']['disabled'] = True
json.dump(d, open('$CONFIG','w'), indent=2)
print(f'⏸️  $2 disabled')
"
      # If all disabled, disable MCP host too
      ALL_OFF=$(python3 -c "
import json
d = json.load(open('$CONFIG'))
all_off = all(cfg.get('disabled',True) for cfg in d['mcpServers'].values())
print('true' if all_off else 'false')
")
      [ "$ALL_OFF" = "true" ] && [ -f "$EXT" ] && mv "$EXT" "${EXT}.disabled" && echo "⏸️  MCP host extension disabled"
    fi
    ;;
  status)
    echo "=== MCP Servers ==="
    python3 -c "
import json
d = json.load(open('$CONFIG'))
for n,c in d['mcpServers'].items():
    s = 'ON' if not c.get('disabled') else 'OFF'
    print(f'  [{s}] {n}')
"
    if [ -f "${EXT}.disabled" ]; then
      echo "  MCP host: OFF"
    else
      echo "  MCP host: ON"
    fi
    ;;
  *)
    echo "Usage: $0 {on|off|status} [server]"
    echo "  Servers: kaggle, colab, sequential-thinking, filesystem, memory, fetch, pdf"
    ;;
esac
