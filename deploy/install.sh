#!/usr/bin/env bash

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
    echo "This script must be run as root." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="/opt/mywebapp"
CONFIG_DIR="/etc/mywebapp"
CONFIG_FILE="${CONFIG_DIR}/config.toml"
SUDOERS_OPERATOR="/etc/sudoers.d/operator"

log_section() {
    echo
    echo "==== $1 ===="
}

ensure_regular_user() {
    local username="$1"
    local add_sudo="$2"

    if id "${username}" >/dev/null 2>&1; then
        echo "User ${username} already exists."
    else
        useradd -m -s /bin/bash "${username}"
        echo "Created user ${username}."
    fi

    echo "${username}:12345678" | chpasswd
    chage -d 0 "${username}"

    if [[ "${add_sudo}" == "yes" ]]; then
        usermod -aG sudo "${username}"
    fi
}

log_section "1) Install required apt packages"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 python3-pip python3-venv nginx postgresql git

log_section "2) Create required users"
if id mywebapp >/dev/null 2>&1; then
    echo "System user mywebapp already exists."
else
    useradd --system --home "${APP_DIR}" --shell /usr/sbin/nologin mywebapp
    echo "Created system user mywebapp."
fi

if id app >/dev/null 2>&1; then
    echo "System user app already exists."
else
    useradd --system --home /nonexistent --shell /usr/sbin/nologin app
    echo "Created system user app."
fi

# Regular lab users with forced password change on first login.
ensure_regular_user student yes
ensure_regular_user teacher yes
# Operator is intentionally non-admin; sudo access is limited via /etc/sudoers.d/operator.
ensure_regular_user operator no
gpasswd -d operator sudo >/dev/null 2>&1 || true

log_section "3) Configure sudo permissions for operator"
cat >"${SUDOERS_OPERATOR}" <<'EOF'
# Purpose: Restrict operator to limited service management commands without password.
operator ALL=(root) NOPASSWD: /bin/systemctl start mywebapp, /bin/systemctl stop mywebapp, /bin/systemctl restart mywebapp, /bin/systemctl status mywebapp, /bin/systemctl reload nginx
EOF
chmod 0440 "${SUDOERS_OPERATOR}"
visudo -cf "${SUDOERS_OPERATOR}"

log_section "4) Configure PostgreSQL user, database, and localhost-only access"
PG_MAIN_DIR="$(find /etc/postgresql -maxdepth 2 -type d -name main | head -n1)"
PG_CONF="${PG_MAIN_DIR}/postgresql.conf"
PG_HBA="${PG_MAIN_DIR}/pg_hba.conf"

if grep -Eq "^#?listen_addresses\s*=" "${PG_CONF}"; then
    sed -ri "s|^#?listen_addresses\s*=.*|listen_addresses = '127.0.0.1'|" "${PG_CONF}"
else
    echo "listen_addresses = '127.0.0.1'" >>"${PG_CONF}"
fi

if ! grep -Eq "^host\s+mywebapp\s+mywebapp\s+127\.0\.0\.1/32\s+scram-sha-256" "${PG_HBA}"; then
    echo "host mywebapp mywebapp 127.0.0.1/32 scram-sha-256" >>"${PG_HBA}"
fi

systemctl restart postgresql

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='mywebapp'" | grep -q 1; then
    echo "PostgreSQL role mywebapp already exists."
else
    sudo -u postgres psql -c "CREATE ROLE mywebapp WITH LOGIN PASSWORD 'mywebapp_password';"
fi

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='mywebapp'" | grep -q 1; then
    echo "Database mywebapp already exists."
else
    sudo -u postgres psql -c "CREATE DATABASE mywebapp OWNER mywebapp;"
fi

log_section "5) Copy repository files to /opt/mywebapp"
install -d "${APP_DIR}"
rm -rf "${APP_DIR}/app" "${APP_DIR}/deploy"
cp -a "${REPO_ROOT}/app" "${APP_DIR}/"
cp -a "${REPO_ROOT}/deploy" "${APP_DIR}/"
cp -a "${REPO_ROOT}/README.md" "${APP_DIR}/"

log_section "6) Create virtualenv and install Python dependencies"
if [[ ! -d "${APP_DIR}/venv" ]]; then
    python3 -m venv "${APP_DIR}/venv"
fi
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/app/requirements.txt"

log_section "7) Create /etc/mywebapp/config.toml"
install -d "${CONFIG_DIR}"
cat >"${CONFIG_FILE}" <<'EOF'
# Purpose: Runtime configuration for mywebapp (lab credentials only).
[server]
host = "127.0.0.1"
port = 8080

[database]
host = "127.0.0.1"
port = 5432
name = "mywebapp"
user = "mywebapp"
password = "mywebapp_password"
EOF

log_section "8) Set ownership to app"
chown -R app:app "${APP_DIR}" "${CONFIG_DIR}"

log_section "9) Install systemd unit files"
cp -a "${REPO_ROOT}/deploy/mywebapp.service" /etc/systemd/system/mywebapp.service
cp -a "${REPO_ROOT}/deploy/mywebapp.socket" /etc/systemd/system/mywebapp.socket

log_section "10) Reload systemd daemon"
systemctl daemon-reload

log_section "11) Enable and start mywebapp socket and service"
systemctl enable --now mywebapp.socket
systemctl enable --now mywebapp.service

log_section "12) Run database migration"
sudo -u app "${APP_DIR}/venv/bin/python" "${APP_DIR}/app/migrate.py"

log_section "13) Install nginx site config"
cp -a "${REPO_ROOT}/deploy/nginx-mywebapp.conf" /etc/nginx/sites-available/mywebapp

log_section "14) Enable nginx site and disable default"
ln -sfn /etc/nginx/sites-available/mywebapp /etc/nginx/sites-enabled/mywebapp
rm -f /etc/nginx/sites-enabled/default

log_section "15) Validate and reload nginx"
nginx -t
systemctl enable --now nginx
systemctl reload nginx

log_section "16) Lock default ubuntu user if present"
# Lock default cloud user after provisioning so only managed lab users can login.
usermod -L ubuntu || true

log_section "17) Create gradebook file"
echo "5" > /home/student/gradebook
chown student:student /home/student/gradebook
chmod 0644 /home/student/gradebook

log_section "18) Print deployment summary"
echo "mywebapp deployed successfully."
echo "- App directory: ${APP_DIR}"
echo "- Config file: ${CONFIG_FILE}"
echo "- systemd socket: mywebapp.socket"
echo "- nginx site: /etc/nginx/sites-available/mywebapp"
systemctl --no-pager --full status mywebapp.service || true
