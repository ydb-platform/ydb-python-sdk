# Notice to external contributors

## Common

YDB is a free and open project and we appreciate to receive contributions from our community.

## Development Environment Setup

### Using Dev Containers (Recommended)

This repository includes a complete development environment using Docker containers that provides everything you need to start contributing immediately. The devcontainer setup includes:

- **Python 3.9** development environment with all necessary dependencies
- **YDB server** running locally in a container
- **Pre-configured tools**: Git, GitHub CLI, YDB CLI, and essential Python packages
- **VS Code extensions**: Python development tools, linting, formatting, and debugging support

#### Prerequisites

- [Docker](https://www.docker.com/get-started) installed and running
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Quick Start with Dev Containers

1. Clone the repository:
   ```bash
   git clone https://github.com/ydb-platform/ydb-python-sdk.git
   cd ydb-python-sdk
   ```

2. Open in VS Code:
   ```bash
   code .
   ```

3. When prompted, click "Reopen in Container" or use the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and select "Dev Containers: Reopen in Container"

4. Wait for the container to build and start (first time may take a few minutes)

5. The development environment is ready! You can now run tests, debug code, and develop new features.

### Using GitHub Codespaces

GitHub Codespaces provides a cloud-based development environment that works directly in your browser or VS Code. It's perfect for quick contributions without setting up a local environment.

#### Quick Start with Codespaces

1. Navigate to the [repository on GitHub](https://github.com/ydb-platform/ydb-python-sdk)
2. Click the green "Code" button
3. Select the "Codespaces" tab
4. Click "Create codespace on main" (or your desired branch)
5. Wait for the environment to initialize (usually 2-3 minutes)
6. Start coding directly in the browser or connect with your local VS Code

#### What's Included in the Development Environment

When you use either dev containers or Codespaces, the following environment is automatically set up:

**Container Services:**
- **SDK Container (`sdk`)**: Your main development environment running Python 3.9 on Debian Bookworm
- **YDB Container (`ydb`)**: Local YDB server (version 25.1) for testing and development

**Development Tools:**
- **YDB CLI**: Pre-installed and configured to connect to the local YDB instance
- **Python Environment**: All project dependencies installed via `pip install -e .`
- **Git Configuration**: Automatic setup for signed commits (if configured)
- **VS Code Extensions**: Python development stack including linting, formatting, and debugging

**Network Configuration:**
- **Port 2135**: YDB gRPC with TLS
- **Port 2136**: YDB gRPC without TLS
- **Port 8765**: YDB Monitoring interface
- These ports are automatically forwarded and accessible from your local machine

**Environment Variables:**
The following environment variables are pre-configured for immediate use:
- `YDB_CONNECTION_STRING=grpc://ydb:2136/local` - Standard connection
- `YDB_CONNECTION_STRING_SECURE=grpcs://ydb:2135/local` - Secure connection
- `YDB_SSL_ROOT_CERTIFICATES_FILE=/ydb_certs/ca.pem` - SSL certificates
- `YDB_STATIC_CREDENTIALS_USER=root` and `YDB_STATIC_CREDENTIALS_PASSWORD=1234` - Test credentials

**Automatic Setup Process:**
1. **Initialize**: Git configuration for signed commits and user settings
2. **Post-Create**: YDB CLI profile setup and GPG configuration for SSH signing
3. **Post-Start**: Installation of Python dependencies, SDK package, and testing tools (tox)

#### Running Tests in the Development Environment

Once your environment is ready, you can run the test suite:

```bash
# Run all tests
tox

# Run specific test categories
python -m pytest tests/

# Run with specific Python version
tox -e py39
```

#### Connecting to the Local YDB Instance

The YDB CLI is pre-configured to connect to the local instance:

```bash
# Run a simple query
echo "SELECT 1;" | ydb

# Access the web interface
# Open http://localhost:8765 in your browser (when using local dev containers)
# In codespaces you can access it via the provided URL in the terminal output.
```

## Contributing code changes

If you would like to contribute a new feature or a bug fix, please discuss your idea first on the GitHub issue.
If there is no issue for your idea, please open one. It may be that somebody is already working on it,
or that there are some complex obstacles that you should know about before starting the implementation.
Usually there are several ways to fix a problem and it is important to find the right approach before spending time on a PR
that cannot be merged.

## Provide a contribution

To make a contribution you should submit a pull request. There will probably be discussion about the pull request and,
if any changes are needed, we would love to work with you to get your pull request merged.

## Other questions

If you have any questions, please mail us at info@ydb.tech.
