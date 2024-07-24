#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interact with the Mealie API via the MealieConnector.
"""

from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone
import meerschaum as mrsm
from meerschaum.config import get_plugin_config, write_plugin_config
from meerschaum.connectors import Connector, make_connector
from meerschaum.actions import make_action

requests = mrsm.attempt_import('requests', venv='mealie')

__version__ = '0.0.1'

required = ['requests']


@make_connector
class MealieConnector(Connector):
    """Implement 'mealie' connectors."""

    REQUIRED_ATTRIBUTES: list[str] = ['token', 'base_url']

    @property
    def headers(self) -> dict[str, str]:
        return {
            'Authorization': f"Bearer {self.token}",
            'Accept': 'application/json',
        }

    def create_backup(self) -> mrsm.SuccessTuple:
        """
        Create a new backup.
        """
        url = urljoin(self.base_url, '/api/admin/backups')
        response = requests.post(url, headers=self.headers, timeout=300)
        if not response:
            return False, f"Failed to create backup:\n{response.text}"

        data = response.json()
        return (not data['error']), data['message']

    def get_latest_backup_name(self) -> str | None:
        """
        Return the filename of the latest backup.
        """
        url = urljoin(self.base_url, '/api/admin/backups')
        response = requests.get(url, headers=self.headers, timeout=30)
        if not response:
            return None
        data = response.json()
        if not data.get('imports'):
            return None

        import_docs = sorted(
            [
                doc
                for doc in data['imports']
            ],
            key=lambda x: x.get('date')
        )
        return import_docs[-1]['name']


@make_action
def backup_mealie(
    connector_keys: list[str] | None = None,
    **kwargs
) -> mrsm.SuccessTuple:
    """Run `mrsm backup mealie` to trigger."""
    if not connector_keys:
        return False, "Specify connector keys with `-c` (e.g. `-c mealie:foo`)."

    ck = connector_keys[0]
    connector = mrsm.get_connector(ck)
    if connector is None:
        return False, f"'{ck}' is not a valid connector."

    success, msg = connector.create_backup()
    if not success:
        return success, msg

    filename = connector.get_latest_backup_name()
    return True, f"Created backup '{filename}'."
