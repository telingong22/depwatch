# depwatch

A daemon that monitors Python and Go project dependencies for new releases and sends digest alerts.

## Installation

```bash
pip install depwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/depwatch.git && cd depwatch && pip install .
```

## Usage

Initialize a config file in your project directory:

```bash
depwatch init
```

Start the daemon to begin monitoring dependencies:

```bash
depwatch start --config depwatch.yaml
```

Example `depwatch.yaml`:

```yaml
projects:
  - name: my-python-app
    path: ./requirements.txt
    type: python
  - name: my-go-service
    path: ./go.mod
    type: go

alerts:
  digest_interval: daily
  email: you@example.com
```

Check for updates immediately without running the daemon:

```bash
depwatch check --config depwatch.yaml
```

Alerts are delivered as digests on your configured schedule, summarizing all new releases across watched dependencies.

## License

MIT © 2024 yourname