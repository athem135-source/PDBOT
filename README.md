## Running the Project with Docker

This project provides Dockerfiles for both the `app` and `src` components, along with a `docker-compose.yml` for orchestrating the services. The setup uses Python 3.13 (for `app`) and Python 3.11 (for `src`), each in a slim container with isolated virtual environments.

### Requirements
- Docker and Docker Compose installed on your system.
- (Optional) `.env` files for environment variables if your application requires them. See the commented `env_file` lines in the compose file for details.

### Build and Run
To build and start all services, run:

```bash
docker compose up --build
```

This will build and start two services:

- **python-app**: Runs the code in `./app` using Python 3.13. No ports are exposed by default. Adjust the Dockerfile or compose file if you need to expose a port.
- **python-src**: Runs the code in `./src` using Python 3.11. Exposes port `8000` internally (not published to the host by default).

Both services share a custom Docker network called `backend` for internal communication.

### Configuration
- If you need to provide environment variables, create a `.env` file in the respective directory and uncomment the `env_file` line in the compose file.
- The default working directory for each service is `/app`.
- The `python-app` service depends on `python-src` and will start after it.

### Ports
- `python-src` exposes port `8000` (internal to the Docker network, not mapped to the host).
- `python-app` does not expose any ports by default.

Adjust the `docker-compose.yml` if you need to publish ports to your host machine for development or production use.
