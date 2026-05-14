# DNS Experiment: musl vs glibc

## Reproduction commands

```bash
# Ubuntu (glibc)
docker run --rm --name dns-ubuntu ubuntu:22.04 bash -lc "apt-get update && apt-get install -y dnsutils && \"\
  \"\"getent hosts myservice\"\" && \"\
  \"\"dig myservice +search\"\""

# Alpine (musl)
docker run --rm --name dns-alpine alpine:3.19 sh -lc "apk add --no-cache bind-tools && \"\
  \"\"getent hosts myservice\"\" && \"\
  \"\"dig myservice +search\"\""
```

## Expected output (Ubuntu)

- Ubuntu/glibc tries multiple search suffixes and then the bare name.
- It issues more DNS queries and may resolve if any suffix matches.

## Expected output (Alpine)

- Alpine/musl appends the search domain once and stops earlier.
- It often fails in environments that rely on multiple search suffix retries.

## Why behavior differs

- Alpine uses musl libc; Debian/Ubuntu use glibc.
- musl only appends the search domain once and does not retry with the bare name
  in the same way glibc does.
- glibc tries more variants (search domain permutations and bare name), so it
  can resolve names that musl fails to resolve.

## Recommendations

- Prefer glibc-based images when your environment relies on DNS search domains.
- Use Alpine when minimal size is critical and service discovery is explicit.
- Consider setting explicit FQDNs or adjust DNS settings if using Alpine.
