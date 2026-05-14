// Seed job should checkout the repository root so readFileFromWorkspace can load the pipeline script.

def pipelinePath = 'jenkins-integration/pipelines/kpi-runner.Jenkinsfile'
def sbtsRelease = 'SBTS26R1'
def defaultTestline = '7_5_UTE5G402T813'
def domains = ['CIT', 'CRT']

domains.each { domainName ->
    folder(domainName) {
        description("${domainName} jobs managed from jenkins-integration/jobs.")
    }

    folder("${domainName}/KPI_Testing") {
        description("KPI testing jobs for ${domainName}.")
    }

    folder("${domainName}/KPI_Testing/${sbtsRelease}") {
        description("KPI testing jobs for ${sbtsRelease}.")
    }

    def jobName = "${domainName}/KPI_Testing/${sbtsRelease}/${defaultTestline}"

    pipelineJob(jobName) {
        description(
            'Python KPI Runner execution entry backed by jenkins-integration/pipelines/kpi-runner.Jenkinsfile. ' +
            'Default repo URLs and credentials come from JCasC/global env, while refs stay job-level configurable.'
        )

        parameters {
            textParam('RUN_REQUEST_JSON', '', 'Optional full python_orchestrator run detail or runner request JSON. RUN_ID + PLATFORM_API_BASE_URL is preferred for platform-api triggers.')
            stringParam('RUN_ID', '', 'platform-api created run_id. Optional for local smoke.')
            stringParam('TESTLINE', defaultTestline, 'Target testline used by runner config resolution.')
            stringParam('WORKFLOW_NAME', 'Python KPI Runner', 'Human-readable workflow name used in request metadata and build display names.')
            textParam('WORKFLOW_SPEC_JSON', '{}', 'WorkflowSpec JSON created by platform-api / automation-portal.')
            stringParam('BUILD', '', 'CIT package / software build under test, for example SBTS26R1.ENB.9999.')
            booleanParam('DRY_RUN', true, 'Run without loading real env_map or TAF bindings.')
            stringParam('RUNNER_REPOSITORY_ROOT', '', 'Optional test-workflow-runner repository root. Defaults to $WORKSPACE/test-workflow-runner.')
            stringParam('RESULT_JSON_PATH', '', 'Optional result JSON path. Defaults to artifacts/python-kpi-runner-result.json.')
            choiceParam('TAF_MODE', ['reuse', 'create-venv', 'skip-install'], 'TAF/python environment mode. reuse expects an existing CIENV, create-venv creates a new CIENV and installs TAF dependencies from robotws, skip-install only skips package installation.')
            stringParam('PYTHON_ENV_ROOT', '', 'Optional Python environment root. Defaults to /home/ute/CIENV/<TESTLINE>.')
            stringParam('PIP_INDEX_URL_OVERRIDE', '', 'Optional pip index URL override for create-venv installs. Falls back to Jenkins global env PIP_INDEX_URL.')
            stringParam('PIP_EXTRA_INDEX_URL_OVERRIDE', '', 'Optional fallback pip index URL override for create-venv installs. Used when PIP_INDEX_URL_OVERRIDE and Jenkins global PIP_INDEX_URL are empty.')
            stringParam('PIP_TRUSTED_HOST_OVERRIDE', '', 'Optional pip trusted-host override for create-venv installs. Falls back to Jenkins global env PIP_TRUSTED_HOST.')
            stringParam('ROBOTWS_ROOT', '', 'Optional explicit robotws root. Useful when workspace layout differs from repo root.')
            stringParam('TESTLINE_VARIABLES_PATH', '', 'Optional explicit testline variable path. Defaults to testline_configuration/<TESTLINE>.')
            stringParam('ROBOTWS_REPO_URL_OVERRIDE', '', 'Optional robotws repo URL override. Default source should come from Jenkins global env / JCasC ROBOTWS_REPO_URL.')
            stringParam('ROBOTWS_GIT_REF', 'master', 'robotws branch/tag/commit. Job-level configurable, current default is master.')
            stringParam('ROBOTWS_CREDENTIALS_ID_OVERRIDE', '', 'Optional robotws credentials override. Default source should come from Jenkins global env / JCasC ROBOTWS_CREDENTIALS_ID.')
            stringParam('TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE', '', 'Optional testline_configuration repo URL override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_REPO_URL.')
            stringParam('TESTLINE_CONFIGURATION_GIT_REF', 'master', 'testline_configuration branch/tag/commit. Job-level configurable, current default is master.')
            stringParam('TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE', '', 'Optional testline_configuration credentials override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_CREDENTIALS_ID.')
            stringParam('ARTIFACT_LABEL', 'kpi-runner', 'Artifact label segment used in request metadata and archive organization.')
            stringParam('RETRY_INDEX', '0', 'Retry index used in artifact directory naming.')
            stringParam('PLATFORM_API_BASE_URL', '', 'Optional platform-api base URL used by request fetch and callback.')
            stringParam('CALLBACK_MAX_ATTEMPTS', '3', 'Maximum callback retry attempts sent by post_run_callback.py.')
            stringParam('CALLBACK_BACKOFF_SECONDS', '2', 'Linear backoff base seconds between callback retries.')
            booleanParam('CALLBACK_IGNORE_FAILURE', true, 'Do not fail the pipeline if callback sending still fails after retries.')
            booleanParam('CALLBACK_INSECURE_TLS', true, 'Skip TLS certificate verification for platform-api callback. Keep enabled when Nginx HTTPS uses a self-signed certificate.')
        }

        definition {
            cps {
                script(readFileFromWorkspace(pipelinePath))
                sandbox(true)
            }
        }
    }
}
