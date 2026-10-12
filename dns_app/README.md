# dns_app – Lab 3, Problem 2

| Folder | Server | Port |
|---|---|---|
| `AS` | Authoritative Server (UDP) | 53533 |
| `FS` | Fibonacci Server (Flask) | 9090 |
| `US` | User Server (Flask) | 8080 |

## Run with Docker

```sh
docker build -t lab3/as AS
docker build -t lab3/fs FS
docker build -t lab3/us US

docker network create lab3net
docker run -d --network lab3net --name as lab3/as
docker run -d --network lab3net --name fs -p 9090:9090 lab3/fs
docker run -d --network lab3net --name us -p 8080:8080 lab3/us

docker inspect lab3net      # look up the AS and FS container IPs
```

## Test

```sh
# 1. Register FS with AS  -> 201
curl -X PUT localhost:9090/register -H "Content-Type: application/json" \
  -d '{"hostname":"fibonacci.com","ip":"<FS_IP>","as_ip":"<AS_IP>","as_port":"53533"}'

# 2. Ask US for a Fibonacci number  -> 200 {"fibonacci":55,"number":10}
curl "localhost:8080/fibonacci?hostname=fibonacci.com&fs_port=9090&number=10&as_ip=<AS_IP>&as_port=53533"
```

A missing parameter on US returns 400, and a non-integer `number` returns 400.
