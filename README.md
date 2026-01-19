# House Watch

HouseWatch is a lightweight, configurable house-monitoring tool that periodically scrapes listings, filters them based on user-defined criteria, and sends notifications when matching houses are found.

The project is designed to run locally or automatically (e.g., via Docker + cron on a server).

---

## Features

- Scrape house listings (e.g. Redfin)
- Flexible filtering (price, property, school, etc.)
- Email notifications
- Configurable via YAML files
- Persistent state to avoid duplicate notifications

---

## Project Structure

HouseWatch has a simple and intuitive structure:

- **configs/** – YAML files for app, criteria, email, etc.
- **data/** – Stores runtime outputs (seen/matched houses), ignored by git
- **src/housewatch/** – Main Python source code
- **tests/** – Integration and regression tests

---

## Configuration

Default configuration files are stored in `configs/` and committed to the repository:

- `app.yaml`
- `criteria.yaml`
- `email.yaml`

For local or environment-specific overrides, create corresponding `.local.yaml` files:

configs/email.local.yaml
configs/app.local.yaml
configs/criteria.local.yaml

If a `.local.yaml` file exists, it will be used **instead of** the default file.
Local config files are ignored by git.

Environment variables can be referenced in YAML using `${VAR_NAME}` and are loaded from `.env`.

---

## Data Directory

The `data/` directory stores runtime outputs (e.g. seen or matched houses).
It is required at runtime but intentionally **not tracked by git**.

## Tests

Tests live under the `tests/` directory and are intended to verify end-to-end behavior (scraping, filtering, and notification flow).

They may generate temporary output in the `data/` directory.

## License

MIT License

## Disclaimer

This project is for personal and educational use only.
Users are responsible for complying with the terms of service of any websites they access.

---

## Running

```bash
python -m housewatch.main
