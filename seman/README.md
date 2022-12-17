# Semantic Search User Files

AInfinity's Semantic Search backend application for livesearch data.

---

### Memory Requirements

The application needs at least 16 GB RAM to run.

### Install and Run

The application requires docker and docker compose to run. Install them.

If you are running the appication on a cpu, run the following:

```sh
$ docker-compose --env-file ./config/.env.cpu up -d
```

If you are running the appication on a gpu, run the following:

```sh
$ docker-compose --env-file ./config/.env.gpu up -d
```

Note: If you want to rebuild the application, add --build .

This will set up two docker containers, one for the api and the other for elasticsearch. It will take some time for the application to set up.

In order to check if the application is ready, run

```sh
$ docker logs <Name of docker container of the api>
```

When you see the following message, the application is ready.

```sh
[2021-06-14 04:41:21 +0000] [10] [INFO] Started server process [10]
[2021-06-14 04:41:21 +0000] [10] [INFO] Waiting for application startup.
[2021-06-14 04:41:21 +0000] [10] [INFO] Application startup complete.
```




Date: 23-08-21

Replicated the semantic-search-livesearch-backend to VM3 from 3.8.211.168:5000 server 
And Made below changes 
    environment:
      - xpack.security.enabled=false
      - discovery.type=single-node
      # - node.name=es01
      # - cluster.name=es-docker-cluster
      # - cluster.initial_master_nodes=es01
      # - bootstrap.memory_lock=true

