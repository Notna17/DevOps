# Lab 2 Report

## Section 1: Python App — Layer Optimization

| Dockerfile | Base Image | Image Size | Rebuild time (code change) | Notes |
|------------|------------|------------|---------------------------|-------|
| v1 naive   | python:3.11-bookworm | TBD | TBD | Deps reinstalled on every code change |
| v2 optimized | python:3.11-bookworm | TBD | TBD | Deps cached |
| v3 alpine  | python:3.11-alpine | TBD | TBD | Smaller, but musl |
| v4 alpine+numpy | python:3.11-alpine | TBD | TBD | numpy wheel issues on alpine |
| v4 debian+numpy | python:3.11-slim | TBD | TBD | numpy prebuilt wheel works |

For each experiment, record:

- Dockerfile path
- Build command
- Environment (OS, Docker version, CPU architecture)

Observations and conclusions:

- Compare rebuild time for v1 vs v2 after a small code change.
- Compare image size differences between Debian slim and Alpine.
- Note numpy build time issues on Alpine (source builds + build tools).
- Recommendation on Alpine vs Debian slim for Python apps.

## Section 2: DNS Behavior — musl vs glibc

Commands run:

- See research/dns-experiment/README.md

Expected output summary:

- Ubuntu/glibc resolves more search domain variants.
- Alpine/musl often stops earlier and can fail.

Explanation:

- musl only appends the search domain once and does not retry the bare name
  as aggressively as glibc.

Recommendations:

- Prefer glibc-based images when DNS search domains are important.
- Use Alpine only with explicit FQDNs or controlled DNS configs.

## Section 3: Golang — Multi-stage Builds

| Dockerfile | Final image size | Has shell? | Can exec in? | Notes |
|------------|------------------|-----------|-------------|-------|
| v1 naive   | TBD | yes | yes | Full Go SDK in image |
| v2 scratch | TBD | no | no | Minimal, CA cert issue |
| v3 distroless | TBD | no | debug variant | Best balance |

Observations and conclusions:

- Compare image sizes for v1 vs v3.
- When to use scratch vs distroless.
- Operational drawbacks of no-shell images.

## Section 4: Docker Compose for Lab 1

- Backend network is internal to isolate the DB.
- Nginx config uses service names (`app`) instead of 127.0.0.1.
- Database persistence uses named volume `postgres_data`.
- Startup order is enforced via healthchecks + depends_on.
- Config file is injected via bind mount, not baked into the image.

## Section 5: General Recommendations

1. Separate dependency installation from code copy in Dockerfiles.
2. Pin dependencies with a lockfile for reproducible builds.
3. Prefer slim images for Python apps with native extensions.
4. Be aware of musl vs glibc DNS differences with Alpine.
5. Use multi-stage builds for compiled languages.
6. Use distroless as a practical default for Go services.
7. Never expose DB ports outside the Docker network.
8. Use healthchecks to gate service startup.
