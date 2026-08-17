# Fase 5 infrastructure gate

The local build is not infrastructure validated. Before enabling external delivery:

1. Publish the Teams app in the organizational catalog and install it for test users.
2. Configure the official Teams authentication middleware for the bot endpoint.
3. Acquire bot access tokens at runtime; never persist them in Airflow or SQLite.
4. Grant only the required Graph app-install permissions and restrict `Mail.Send` to a dedicated mailbox.
5. Replace SQLite if the bot runs with multiple replicas or requires a managed HA database.
6. Exercise one real delivery, approval, replay, expiry, rejection, Outlook fallback and stale MLflow precondition.

`teams-app-manifest.json` contains placeholders that deployment tooling must substitute. It is not deployable as-is.
