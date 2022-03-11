host="192.168.1.2"

# Quickfix IPv6 formatting
if host.count(':') > 2:
  host = f"[{host}]"
print(host)

host="2ffe:abc:def::1"
# Quickfix IPv6 formatting
if host.count(':') > 2:
  host = f"[{host}]"
print(host)

host="something.local"
# Quickfix IPv6 formatting
if host.count(':') > 2:
  host = f"[{host}]"
print(host)

