"""DEPRECATED / UNUSED.

This module was an orphaned duplicate of `app.api.hardware_agent` (no
`backend/app/routers/__init__.py` exists, and nothing imports `app.routers`,
so this router was never mounted into the FastAPI application).

It also referenced files that no longer match the installer package
(`README.txt` instead of `README_installer.txt`, and it was missing
`setup_wizard.py` / `Kickerkasse-Install.desktop` from its ZIP contents).

The single source of truth for the Hardware-Agent API is now exclusively
`backend/app/api/hardware_agent.py` (registered in `backend/app/api/__init__.py`).

Kept as an emptied stub instead of being deleted because the sandbox this
change was authored in could not unlink the file; the file has no imports
into the running application and can be safely removed by a maintainer in a
later cleanup commit.
"""
