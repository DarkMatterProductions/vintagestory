"""
Airflow DAG: Detects when an API's reported version changes, then calls out to
other APIs — with OpenLineage lineage reporting on the HTTP endpoints involved.

WHY IT'S STRUCTURED THIS WAY
-----------------------------
1. get_baseline_version    (PythonOperator)
   Reads the last known version from an Airflow Variable and pushes it to XCom.
   Fixes the baseline for the whole DAG run so it doesn't shift mid-poll.

2. wait_for_version_change (LineageHttpSensor, poke mode)
   Polls the API endpoint. response_check() compares the current version
   against the baseline and succeeds as soon as they differ.

3. run_on_version_change   (LineagePythonOperator)
   Calls downstream APIs (GET/POST) once a new version is detected.

4. update_stored_version   (PythonOperator)
   Persists the newly detected version so the *next* DAG run compares
   against an up-to-date baseline.

OPENLINEAGE / LINEAGE SUPPORT
------------------------------
Every task in an Airflow DAG automatically emits a basic OpenLineage
START/COMPLETE event once the provider below is installed and configured —
that's what makes the DAG and its tasks show up as a *job* in your lineage
UI (Marquez/DataHub/etc.) with no code changes.

What does NOT happen automatically: HttpSensor and PythonOperator have no
built-in OpenLineage extractor, so the actual API endpoints they talk to
won't show up as *dataset* nodes (the boxes lineage tools draw lines
between) unless we tell OpenLineage about them explicitly. That's what
LineageHttpSensor and LineagePythonOperator below do, via the
get_openlineage_facets_on_start / get_openlineage_facets_on_complete hooks
that the OpenLineage provider looks for on every operator.

SETUP (do this once per Airflow environment)
----------------------------------------------
1. pip install apache-airflow-providers-openlineage

2. Configure where events get sent — airflow.cfg or env vars. Example for
   Marquez running locally:

     [openlineage]
     transport = {"type": "http", "url": "http://localhost:5000", "endpoint": "api/v1/lineage"}
     namespace = my-team-airflow

   or as env vars:

     AIRFLOW__OPENLINEAGE__TRANSPORT='{"type": "http", "url": "http://localhost:5000", "endpoint": "api/v1/lineage"}'
     AIRFLOW__OPENLINEAGE__NAMESPACE='my-team-airflow'

   DataHub and Astronomer/Astro accept the same "http" transport shape —
   just swap the url/endpoint for whatever your backend's OpenLineage
   ingestion endpoint is (check its docs for the exact path).

3. Restart the scheduler/workers after installing so the provider's Airflow
   plugin (which listens for task start/complete events) gets picked up.

NAMING CONVENTION USED FOR HTTP DATASETS
------------------------------------------
OpenLineage has an official naming convention for databases/object stores,
but not for generic REST/HTTP APIs. This DAG uses a simple, consistent
convention so endpoints line up across jobs:
    namespace = "<scheme>://<host>[:<port>]"
    name      = "<path>"
e.g. GET https://api.example.com/v2/version ->
    namespace="https://api.example.com", name="/v2/version"
Pick whatever convention you like, but keep it consistent across all DAGs
that talk to the same APIs, or the lineage graph won't connect them.

BEFORE RUNNING
--------------
- Create an Airflow connection (Admin -> Connections) with ID = HTTP_CONN_ID,
  pointing to your API's base host (e.g. https://api.example.com).
- Adjust ENDPOINT to the path that returns the version.
- check_version_changed() assumes the endpoint returns the version as a bare
  string (e.g. "1.4.2"), not JSON.
- run_on_version_change()'s API calls below are placeholders — replace with
  your real GET/POST calls; lineage is captured automatically as long as
  you make the calls through the `session` object passed in.
- Requires apache-airflow-providers-http and apache-airflow-providers-openlineage.
- Written for Airflow 2.4+ (uses `schedule=`). Confirm get_openlineage_facets_on_*
  hooks are supported by whatever openlineage provider version you install —
  check its changelog for your Airflow version.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import urlsplit

import requests
from airflow import DAG
from airflow.hooks.base import BaseHook
from airflow.models import Variable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.http.sensors.http import HttpSensor

# ---------------------------------------------------------------------------
# Config — edit these for your environment
# ---------------------------------------------------------------------------
HTTP_CONN_ID = "vintage_story_api"                 # Airflow connection ID (host/auth live here)
ENDPOINT = "latestunstable.txt"                     # path relative to the connection's host
VARIABLE_KEY = "vintage_story_unstable_version"    # Airflow Variable used to persist state

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


# ---------------------------------------------------------------------------
# Lineage helpers
# ---------------------------------------------------------------------------
def _http_dataset(url: str):
    """Build an OpenLineage Dataset for a URL using the namespace/name
    convention documented above. Imports lazily so this module still loads
    fine if the openlineage client isn't installed in some environment."""
    from openlineage.client.run import Dataset

    parts = urlsplit(url)
    namespace = f"{parts.scheme}://{parts.netloc}"
    name = parts.path or "/"
    return Dataset(namespace=namespace, name=name)


def _connection_base_url(conn_id: str) -> str:
    """Reconstruct a base URL (scheme://host[:port]) from an Airflow HTTP connection."""
    conn = BaseHook.get_connection(conn_id)
    scheme = conn.schema or "https"
    port = f":{conn.port}" if conn.port else ""
    return f"{scheme}://{conn.host}{port}"


class LineageHttpSensor(HttpSensor):
    """HttpSensor that reports the endpoint it polls as an OpenLineage input dataset."""

    def get_openlineage_facets_on_start(self):
        from airflow.providers.openlineage.extractors import OperatorLineage

        base_url = _connection_base_url(self.http_conn_id)
        url = f"{base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"
        return OperatorLineage(inputs=[_http_dataset(url)])


class LineageTrackingSession(requests.Session):
    """A requests.Session that records every call made through it, so
    LineagePythonOperator can report them as lineage after the task runs."""

    def __init__(self):
        super().__init__()
        self.calls: list[tuple[str, str]] = []  # [(method, url), ...]

    def request(self, method, url, *args, **kwargs):  # noqa: D102
        self.calls.append((method.upper(), url))
        return super().request(method, url, *args, **kwargs)


class LineagePythonOperator(PythonOperator):
    """PythonOperator that injects a LineageTrackingSession into
    op_kwargs["session"]. Write your API calls using that session (instead
    of bare `requests`) and this operator will automatically report each
    call as an OpenLineage dataset once the task completes:
        GET              -> input dataset
        POST/PUT/PATCH/DELETE -> output dataset
    """

    def execute(self, context):
        self._lineage_session = LineageTrackingSession()
        self.op_kwargs = {**(self.op_kwargs or {}), "session": self._lineage_session}
        return super().execute(context)

    def get_openlineage_facets_on_complete(self, task_instance):
        from airflow.providers.openlineage.extractors import OperatorLineage

        inputs, outputs = [], []
        for method, url in getattr(self, "_lineage_session", LineageTrackingSession()).calls:
            dataset = _http_dataset(url)
            (inputs if method == "GET" else outputs).append(dataset)
        return OperatorLineage(inputs=inputs, outputs=outputs)


# ---------------------------------------------------------------------------
# Task callables
# ---------------------------------------------------------------------------
def get_baseline_version(**context):
    """Read the last known version from an Airflow Variable and push it to XCom."""
    baseline = Variable.get(VARIABLE_KEY, default_var=None)
    context["ti"].xcom_push(key="baseline_version", value=baseline)
    print(f"Baseline version for this run: {baseline!r}")


def check_version_changed(response, **context):
    """response_check callback for HttpSensor.

    Returns True (sensor succeeds) as soon as the version in the API response
    differs from the baseline captured at the start of this DAG run.
    """
    baseline = context["ti"].xcom_pull(
        task_ids="get_baseline_version", key="baseline_version"
    )

    current_version = response.text.strip()  # endpoint returns a bare string, e.g. "1.4.2"

    context["ti"].xcom_push(key="current_version", value=current_version)

    print(f"Baseline={baseline!r} Current={current_version!r}")
    return baseline != current_version


def call_downstream_apis(session: LineageTrackingSession, **context):
    """Placeholder for your real GET/POST logic against various APIs.
    Route every call through `session` (not bare `requests`) so
    LineagePythonOperator can report it as lineage automatically."""
    new_version = context["ti"].xcom_pull(
        task_ids="wait_for_version_change", key="current_version"
    )

    # Example: notify one service, then fetch a related resource from another.
    session.post(
        "https://notifications.example.com/api/notify",
        json={"event": "version_changed", "version": new_version},
    )
    session.get("https://inventory.example.com/api/dependents")


def update_stored_version(**context):
    """Persist the newly detected version so the next DAG run has a fresh baseline."""
    new_version = context["ti"].xcom_pull(
        task_ids="wait_for_version_change", key="current_version"
    )
    Variable.set(VARIABLE_KEY, new_version)
    print(f"Stored new baseline version: {new_version!r}")


with DAG(
        dag_id="build_vs_docker_unstable",
        description="Polls an API for a version string and reacts when it changes",
        default_args=default_args,
        schedule=timedelta(minutes=60),
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["http-sensor", "openlineage", "vintagestory", "docker"],
) as dag:

    get_baseline_version_task = PythonOperator(
        task_id="get_baseline_version",
        python_callable=get_baseline_version,
    )

    wait_for_version_change = LineageHttpSensor(
        task_id="wait_for_version_change",
        http_conn_id=HTTP_CONN_ID,
        endpoint=ENDPOINT,
        method="GET",
        response_check=check_version_changed,
        soft_fail=True,
        poke_interval=60,      # seconds between checks
        timeout=60 * 2,   # give up after 2 minutes
        mode="poke",           # classic sensor: occupies a worker slot the whole time
    )

    run_on_version_change = LineagePythonOperator(
        task_id="run_on_version_change",
        python_callable=call_downstream_apis,
    )

    update_stored_version_task = PythonOperator(
        task_id="update_stored_version",
        python_callable=update_stored_version,
    )

    (
            get_baseline_version_task
            >> wait_for_version_change
            >> run_on_version_change
            >> update_stored_version_task
    )