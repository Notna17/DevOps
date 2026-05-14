# Laboratory Work #1 - mywebapp

## 1. Variant Calculation (N=5)

- `V2 = (N % 2) + 1 = (5 % 2) + 1 = 2`
- `V3 = (N % 3) + 1 = (5 % 3) + 1 = 3`
- `V5 = (N % 5) + 1 = (5 % 5) + 1 = 1`

Results:

- `V2=2`: configuration file `/etc/mywebapp/config.toml` + PostgreSQL
- `V3=3`: Simple Inventory web application
- `V5=1`: application listens on port `8080`

## 2. Application Description

`mywebapp` is a Python Flask backend for a simple inventory.

Inventory item fields:

- `id` (auto-increment primary key)
- `name` (text, required)
- `quantity` (integer, required)
- `created_at` (timestamp, default current time)

Business endpoints:

- `GET /items`
- `POST /items`
- `GET /items/<id>`

Health endpoints:

- `GET /health/alive`
- `GET /health/ready`

Root endpoint:

- `GET /` returns HTML endpoint overview

## 3. Development Environment Setup

Local development can be done on Linux with PostgreSQL installed locally.

1. Install prerequisites:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql
```

2. Create DB role and database:

```bash
sudo -u postgres psql -c "CREATE ROLE mywebapp WITH LOGIN PASSWORD 'mywebapp_password';" || true
sudo -u postgres psql -c "CREATE DATABASE mywebapp OWNER mywebapp;" || true
```

3. Create config file:

```bash
sudo mkdir -p /etc/mywebapp
sudo tee /etc/mywebapp/config.toml >/dev/null <<'EOF'
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
```

4. Create virtualenv and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r app/requirements.txt
```

5. Run migration:

```bash
python app/migrate.py
```

6. Start app:

```bash
python app/app.py
```

## 4. How To Run App Manually

From repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r app/requirements.txt
python app/migrate.py
python app/app.py
```

The app serves on `127.0.0.1:8080` (or via systemd socket activation when deployed).

## 5. Running with Docker Compose

### Prerequisites

- Docker >= 24.0
- Docker Compose v2 (plugin)

### Clone the repo

```bash
git clone <your-repo-url>
cd DevOps
```

### Start the stack

```bash
docker compose up -d --build
```

### Check status and logs

```bash
docker compose ps
docker compose logs -f
```

### Test the running system

```bash
# Health checks
curl http://localhost/health/alive
curl http://localhost/
curl http://localhost/items
curl -X POST http://localhost/items \
	-H "Content-Type: application/json" \
	-d '{"name": "Laptop", "quantity": 5}'
curl http://localhost/items/1
curl -H "Accept: text/html" http://localhost/items
```

### Stop and clean up

```bash
docker compose down
docker compose down -v
```

### Architecture diagram

```
HOST
 └─ port 80
		 └─ [frontend network]
				 └─ nginx
						 └─ [backend network] (internal, no internet)
								 ├─ app (Flask + gunicorn)
								 └─ db  (PostgreSQL, named volume)
```

### Data persistence

The `postgres_data` volume persists database state across restarts. Only `docker compose down -v` removes it.

### Base image choice

The app image uses `python:3.11-slim` instead of Alpine because many Python packages rely on glibc-based
prebuilt wheels; Debian slim avoids musl-related build issues and reduces the need for compile toolchains.

## 6. API Documentation

### Content Negotiation Rules

- Business endpoints: `/items`, `/items/<id>`
- `Accept: application/json` -> JSON
- `Accept: text/html` -> HTML (`/items` uses `<table>`)
- No `Accept` or `*/*` -> JSON by default

### Endpoint Table

| Method | Path | Description | Request Body |
|---|---|---|---|
| GET | `/` | HTML page listing endpoints | none |
| GET | `/health/alive` | Liveness probe, always `200 OK` with `OK` | none |
| GET | `/health/ready` | Readiness probe, checks DB connectivity | none |
| GET | `/items` | List all items (`id`, `name`) | none |
| POST | `/items` | Create item | `{"name":"Keyboard","quantity":10}` |
| GET | `/items/<id>` | Item details (`id`, `name`, `quantity`, `created_at`) | none |

### Example Responses

`GET /items` (`Accept: application/json`):

```json
[
	{
		"id": 1,
		"name": "Keyboard"
	}
]
```

`GET /items` (`Accept: text/html`):

```html
<!doctype html>
<html>
	<body>
		<h1>Inventory items</h1>
		<table border="1">
			<thead><tr><th>id</th><th>name</th></tr></thead>
			<tbody>
				<tr><td>1</td><td>Keyboard</td></tr>
			</tbody>
		</table>
	</body>
</html>
```

`POST /items` (`Accept: application/json`):

```json
{
	"id": 1,
	"name": "Keyboard",
	"quantity": 10,
	"created_at": "2026-04-11T10:00:00+00:00"
}
```

`POST /items` (`Accept: text/html`):

```html
<!doctype html>
<html>
	<body>
		<h1>Inventory item 1</h1>
		<table border="1">
			<tbody>
				<tr><th>id</th><td>1</td></tr>
				<tr><th>name</th><td>Keyboard</td></tr>
				<tr><th>quantity</th><td>10</td></tr>
				<tr><th>created_at</th><td>2026-04-11T10:00:00+00:00</td></tr>
			</tbody>
		</table>
	</body>
</html>
```

`GET /items/1` (`Accept: application/json`):

```json
{
	"id": 1,
	"name": "Keyboard",
	"quantity": 10,
	"created_at": "2026-04-11T10:00:00+00:00"
}
```

`GET /items/1` (`Accept: text/html`):

```html
<!doctype html>
<html>
	<body>
		<h1>Inventory item 1</h1>
		<table border="1">
			<tbody>
				<tr><th>id</th><td>1</td></tr>
				<tr><th>name</th><td>Keyboard</td></tr>
				<tr><th>quantity</th><td>10</td></tr>
				<tr><th>created_at</th><td>2026-04-11T10:00:00+00:00</td></tr>
			</tbody>
		</table>
	</body>
</html>
```

## 7. Deployment Documentation

### Base VM image

- OS: Ubuntu 22.04 LTS
- Official link: https://releases.ubuntu.com/22.04/

### Minimum VM resources

- CPU: 1 core
- RAM: 1 GB
- Disk: 10 GB

### Special OS setup

- No special pre-setup is required.
- Use the default Ubuntu cloud/desktop user (commonly `ubuntu`) before running installer.

### SSH into VM

```bash
ssh ubuntu@<VM_IP>
```

### Clone and deploy

Automation entrypoint (single command script): `deploy/install.sh`.

```bash
git clone <your-repo-url>
cd DevOps
sudo bash deploy/install.sh
```

What `deploy/install.sh` does:

- installs required packages (`python3`, `python3-pip`, `python3-venv`, `nginx`, `postgresql`, `git`)
- creates users: `student`, `teacher`, `operator`, `mywebapp`, `app`
- creates PostgreSQL role/database and local-only DB access
- installs systemd units (`mywebapp.service`, `mywebapp.socket`)
- runs migrations and starts service
- configures nginx reverse proxy
- creates `/home/student/gradebook` with value `5`
- locks default `ubuntu` user

### systemd mode switching

Socket activation mode (default deployment path):

```bash
sudo systemctl enable --now mywebapp.socket
sudo systemctl restart mywebapp.service
```

Direct service mode (service binds `server.host`/`server.port` from config):

```bash
sudo systemctl disable --now mywebapp.socket
sudo systemctl restart mywebapp.service
```

Return to socket activation:

```bash
sudo systemctl enable --now mywebapp.socket
sudo systemctl restart mywebapp.service
```

## 8. Testing Instructions (Exact curl commands)

`GET /health/alive`:

```bash
curl -i http://127.0.0.1:8080/health/alive
```

`GET /health/ready`:

```bash
curl -i http://127.0.0.1:8080/health/ready
```

`GET /items` JSON:

```bash
curl -i -H 'Accept: application/json' http://127.0.0.1:8080/items
```

`GET /items` HTML:

```bash
curl -i -H 'Accept: text/html' http://127.0.0.1:8080/items
```

`POST /items`:

```bash
curl -i -X POST http://127.0.0.1:8080/items \
	-H 'Content-Type: application/json' \
	-H 'Accept: application/json' \
	-d '{"name":"Keyboard","quantity":10}'
```

`GET /items/1`:

```bash
curl -i -H 'Accept: application/json' http://127.0.0.1:8080/items/1
```

Check that `/health/alive` is blocked externally by nginx:

```bash
curl -i http://<VM_IP>/health/alive
```

Expected: `404 Not Found`.

Verify operator restrictions:

```bash
ssh operator@<VM_IP>
sudo systemctl status mywebapp
sudo systemctl restart mywebapp
sudo apt update
```

Expected:

- `sudo systemctl status mywebapp` works
- `sudo systemctl restart mywebapp` works
- `sudo apt update` is denied

Additional deployment verification:

```bash
sudo systemctl status mywebapp.socket --no-pager
sudo systemctl status mywebapp.service --no-pager
sudo systemctl status nginx --no-pager
cat /home/student/gradebook
```

Expected:

- both `mywebapp.socket` and `mywebapp.service` are active (or service active after first request)
- nginx is active
- `gradebook` prints exactly `5`

## 9. Config File Format (`/etc/mywebapp/config.toml`)

TOML was chosen because it is human-readable, strict enough to reduce syntax mistakes, and maps naturally to structured sections (`[server]`, `[database]`) without external parser complexity.

Example:

```toml
[server]
host = "127.0.0.1"
port = 8080

[database]
host = "127.0.0.1"
port = 5432
name = "mywebapp"
user = "mywebapp"
password = "mywebapp_password"
```

Key descriptions:

- `server.host`: interface/address used in direct service mode
- `server.port`: app listening port in direct service mode
- `database.host`: PostgreSQL host
- `database.port`: PostgreSQL port
- `database.name`: database name
- `database.user`: PostgreSQL user
- `database.password`: PostgreSQL password

Note: static credentials in this lab are for educational use only and must be replaced in production.