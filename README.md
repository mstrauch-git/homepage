# Academic homepage with ORCID Works importer

Files:
- `index.html`: original design and navigation, with a publications display.
- `scripts/update_orcid.py`: retrieves only publicly visible ORCID Works.
- `.github/workflows/update-publications.yml`: manual or monthly update.
- `publications.json`: created by first successful workflow run.

## Install
Upload the contents of this ZIP to the **root** of the private `homepage` GitHub repository, preserving the `.github/workflows` and `scripts` directories. Keep your existing GitHub Actions secrets `ORCID_CLIENT_ID` and `ORCID_CLIENT_SECRET`.

In GitHub Actions, select **Update ORCID publications** and click **Run workflow**. When the run succeeds, `publications.json` is committed automatically. Refresh the Codespaces browser preview (running `python3 -m http.server 8000`) to see the bibliography. If the Codespace was already open, use `git pull` in its terminal to obtain the new file.

The schedule is the first of every month at 09:17 UTC. GitHub scheduled workflows can be delayed and may be disabled after repository inactivity. You can always trigger a manual run.

If the workflow cannot push due to repository settings, check Settings > Actions > General > Workflow permissions and allow read/write permissions, or use a manual commit instead.

ORCID may omit author lists, journal names or dates for some Works. Entries display only metadata actually provided. Duplicate groupings are collapsed. The workflow leaves the last successful JSON file intact if the import fails.
