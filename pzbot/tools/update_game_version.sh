#!/bin/bash
# update_game.sh
# Usage: ./update_game.sh [beta_branch]

BRANCH=$1
BETA_FLAG=""
INSTALL_DIR="/root/Zomboid"

if [ ! -z "$BRANCH" ]; then
    echo "[Updater] Switching to Beta Branch: $BRANCH"
    BETA_FLAG="-beta $BRANCH"
fi

echo "----------------------------------------------------------------"
echo "Project Zomboid Client Update (AppID 380870)"
echo "Target Directory: $INSTALL_DIR"
echo "Branch: ${BRANCH:-Stable}"
echo "----------------------------------------------------------------"
echo "WARNING: You will need to provide your Steam Password (and Steam Guard code)!"
echo ""
read -p "Enter Steam Username: " STEAM_USER

if [ -z "$STEAM_USER" ]; then
    echo "Error: Username required."
    exit 1
fi

# Run SteamCMD interactively
/root/steamcmd/steamcmd.sh \
    +force_install_dir "$INSTALL_DIR" \
    +login "$STEAM_USER" \
    +app_update 380870 $BETA_FLAG validate \
    +quit

echo "----------------------------------------------------------------"
echo "Update process finished."
