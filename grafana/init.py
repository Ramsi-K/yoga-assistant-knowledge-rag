"""
Grafana initialization script for Yoga Assistant system.

This script:
1. Creates a PostgreSQL datasource in Grafana
2. Imports the monitoring dashboard

Usage:
    python grafana/init.py

Environment Variables:
    GRAFANA_URL: Grafana URL (default: http://localhost:3000)
    GRAFANA_USER: Grafana admin username (default: admin)
    GRAFANA_PASSWORD: Grafana admin password (default: admin)
    POSTGRES_HOST: PostgreSQL host (default: localhost)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_DB: PostgreSQL database name (default: yoga_rag)
    POSTGRES_USER: PostgreSQL username (default: postgres)
    POSTGRES_PASSWORD: PostgreSQL password
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_grafana_config() -> Dict[str, str]:
    """
    Get Grafana configuration from environment variables.

    Returns:
        Dictionary with Grafana connection details
    """
    return {
        "url": os.getenv("GRAFANA_URL", "http://localhost:3000"),
        "user": os.getenv("GRAFANA_USER", "admin"),
        "password": os.getenv("GRAFANA_PASSWORD", "admin"),
    }


def get_postgres_config() -> Dict[str, str]:
    """
    Get PostgreSQL configuration from environment variables.

    Returns:
        Dictionary with PostgreSQL connection details
    """
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "yoga_rag"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
    }


def wait_for_grafana(url: str, max_retries: int = 30, delay: int = 2) -> bool:
    """
    Wait for Grafana to be ready.

    Args:
        url: Grafana URL
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        True if Grafana is ready, False otherwise
    """
    print(f"Waiting for Grafana at {url}...")

    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✓ Grafana is ready")
                return True
        except requests.exceptions.RequestException:
            pass

        if i < max_retries - 1:
            print(f"  Attempt {i + 1}/{max_retries} - waiting {delay}s...")
            time.sleep(delay)

    print("✗ Grafana did not become ready in time")
    return False


def create_datasource(
    grafana_config: Dict[str, str], postgres_config: Dict[str, str]
) -> bool:
    """
    Create PostgreSQL datasource in Grafana.

    Args:
        grafana_config: Grafana connection details
        postgres_config: PostgreSQL connection details

    Returns:
        True if successful, False otherwise
    """
    print("\nCreating PostgreSQL datasource...")

    url = f"{grafana_config['url']}/api/datasources"
    auth = (grafana_config["user"], grafana_config["password"])

    # When Grafana runs in Docker, use service name instead of localhost
    postgres_host = postgres_config["host"]
    if postgres_host == "localhost":
        postgres_host = "postgres"

    datasource_payload = {
        "name": "Yoga RAG PostgreSQL",
        "type": "grafana-postgresql-datasource",
        "access": "proxy",
        "url": f"{postgres_host}:{postgres_config['port']}",
        "database": postgres_config["database"],
        "user": postgres_config["user"],
        "secureJsonData": {"password": postgres_config["password"]},
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 1500,
            "timescaledb": False,
        },
        "isDefault": True,
    }

    try:
        # Check if datasource already exists
        response = requests.get(url, auth=auth, timeout=10)
        if response.status_code == 200:
            datasources = response.json()
            for ds in datasources:
                if ds.get("name") == "Yoga RAG PostgreSQL":
                    print("✓ Datasource already exists")
                    return True

        # Create new datasource
        response = requests.post(
            url, auth=auth, json=datasource_payload, timeout=10
        )

        if response.status_code in [200, 201]:
            print("✓ Datasource created successfully")
            return True
        else:
            print(f"✗ Failed to create datasource: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Error creating datasource: {str(e)}")
        return False


def import_dashboard(grafana_config: Dict[str, str]) -> bool:
    """
    Import monitoring dashboard into Grafana.

    Args:
        grafana_config: Grafana connection details

    Returns:
        True if successful, False otherwise
    """
    print("\nImporting dashboard...")

    # Load dashboard JSON
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.json")

    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            dashboard_data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Dashboard file not found: {dashboard_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in dashboard file: {str(e)}")
        return False

    url = f"{grafana_config['url']}/api/dashboards/db"
    auth = (grafana_config["user"], grafana_config["password"])

    # Prepare payload
    payload = {
        "dashboard": dashboard_data.get("dashboard", dashboard_data),
        "overwrite": True,
        "message": "Imported by init script",
    }

    try:
        response = requests.post(url, auth=auth, json=payload, timeout=10)

        if response.status_code in [200, 201]:
            result = response.json()
            dashboard_url = f"{grafana_config['url']}{result.get('url', '')}"
            print("✓ Dashboard imported successfully")
            print(f"  Dashboard URL: {dashboard_url}")
            return True
        else:
            print(f"✗ Failed to import dashboard: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Error importing dashboard: {str(e)}")
        return False


def verify_setup(grafana_config: Dict[str, str]) -> bool:
    """
    Verify that Grafana setup is complete.

    Args:
        grafana_config: Grafana connection details

    Returns:
        True if setup is valid, False otherwise
    """
    print("\nVerifying setup...")

    auth = (grafana_config["user"], grafana_config["password"])

    try:
        # Check datasources
        response = requests.get(
            f"{grafana_config['url']}/api/datasources", auth=auth, timeout=10
        )
        if response.status_code != 200:
            print("✗ Failed to verify datasources")
            return False

        datasources = response.json()
        postgres_ds = any(
            ds.get("name") == "Yoga RAG PostgreSQL" for ds in datasources
        )

        if not postgres_ds:
            print("✗ PostgreSQL datasource not found")
            return False

        print("✓ Datasource verified")

        # Check dashboards
        response = requests.get(
            f"{grafana_config['url']}/api/search?type=dash-db",
            auth=auth,
            timeout=10,
        )
        if response.status_code != 200:
            print("✗ Failed to verify dashboards")
            return False

        dashboards = response.json()
        yoga_dashboard = any(
            d.get("uid") == "yoga-rag-dashboard" for d in dashboards
        )

        if not yoga_dashboard:
            print("✗ Yoga RAG dashboard not found")
            return False

        print("✓ Dashboard verified")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Error verifying setup: {str(e)}")
        return False


def main():
    """
    Main function to initialize Grafana.

    Steps:
    1. Wait for Grafana to be ready
    2. Create PostgreSQL datasource
    3. Import monitoring dashboard
    4. Verify setup
    """
    print("=" * 60)
    print("Yoga Assistant - Grafana Initialization")
    print("=" * 60)
    print()

    # Get configuration
    grafana_config = get_grafana_config()
    postgres_config = get_postgres_config()

    # Validate PostgreSQL password
    if not postgres_config["password"]:
        print("✗ POSTGRES_PASSWORD environment variable is required")
        sys.exit(1)

    # Wait for Grafana
    if not wait_for_grafana(grafana_config["url"]):
        print("\n✗ Failed to connect to Grafana")
        print(f"  Make sure Grafana is running at {grafana_config['url']}")
        sys.exit(1)

    # Create datasource
    if not create_datasource(grafana_config, postgres_config):
        print("\n✗ Failed to create datasource")
        sys.exit(1)

    # Import dashboard
    if not import_dashboard(grafana_config):
        print("\n✗ Failed to import dashboard")
        sys.exit(1)

    # Verify setup
    if not verify_setup(grafana_config):
        print("\n✗ Setup verification failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ Grafana initialization complete!")
    print("=" * 60)
    print()
    print(f"Dashboard URL: {grafana_config['url']}/d/yoga-rag-dashboard")
    print(f"Username: {grafana_config['user']}")
    print(f"Password: {grafana_config['password']}")
    print()


if __name__ == "__main__":
    main()
