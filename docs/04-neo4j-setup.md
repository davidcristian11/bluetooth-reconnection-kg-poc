# Neo4j Local Setup

This project runs Neo4j CE locally using Docker Desktop and Docker Compose.

## Prerequisites

Install and start:

* Docker Desktop
* WSL 2, used by Docker Desktop for Linux containers

Verify that Docker is working:

```powershell
docker version
docker compose version
```

The `docker version` output should contain both `Client` and `Server` sections.

## Environment Configuration

Create a local `.env` file in the repository root:

```text
NEO4J_PASSWORD=your-local-password
```

The `.env` file contains a local secret and must not be committed to Git.

The tracked `.env.example` file documents the required variable without containing a real password:

```text
NEO4J_PASSWORD=replace-with-your-local-password
```

## Docker Compose Configuration

Neo4j is configured in the repository root using `compose.yaml`.

The configuration:

* uses Neo4j Community Edition;
* exposes the Neo4j web interface on port `7474`;
* exposes the Bolt database connection on port `7687`;
* stores database files in the persistent `neo4j_data` volume;
* mounts the repository's `data/` directory as Neo4j's read-only `/import` directory.

The data mapping is:

```text
Repository: ./data
Container:  /import
Access:     read-only
```

## Start Neo4j

From the repository root, validate the Compose configuration:

```powershell
docker compose config --quiet
```

Start Neo4j in the background:

```powershell
docker compose up -d
```

Check its status:

```powershell
docker compose ps
```

View recent startup logs:

```powershell
docker compose logs --tail 50 neo4j
```

Neo4j is ready when the logs contain:

```text
Started.
```

## Open Neo4j Query

Open the following address:

```text
http://localhost:7474
```

Use:

```text
Connection URL: neo4j://localhost:7687
Username:       neo4j
Password:       value from the local .env file
Database:       neo4j
```

The `neo4j` database is the normal database used by this PoC. The internal `system` database is not used for project graph data.

## Stop and Restart Neo4j

Stop the existing container without removing it:

```powershell
docker compose stop
```

Start the same container again:

```powershell
docker compose start
```

Stop and remove the container and Compose network:

```powershell
docker compose down
```

The named `neo4j_data` volume is preserved by `docker compose down`, so the database can be reused when the container is recreated.

Start or recreate the container:

```powershell
docker compose up -d
```

Do not run the following command unless the database data should be permanently deleted:

```powershell
docker compose down -v
```

The `-v` option removes the persistent volume.

## Verify CSV Access

List the repository files visible inside the Neo4j container:

```powershell
docker compose exec neo4j find /import -maxdepth 2 -type f
```

A repository file such as:

```text
data/nodes/features.csv
```

is available to Neo4j as:

```text
file:///nodes/features.csv
```

A CSV can be previewed without creating graph data:

```cypher
LOAD CSV WITH HEADERS
FROM "file:///nodes/features.csv" AS row
RETURN row
LIMIT 3;
```

The complete synthetic dataset is not imported during this setup step. Its nodes and relationships will be imported in the next project step.
