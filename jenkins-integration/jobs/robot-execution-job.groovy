// Seed job should checkout the repository root so readFileFromWorkspace can load the pipeline script.

def jobFolder = 'robot'
def jobName = "${jobFolder}/robot-execution"
def pipelinePath = 'jenkins-integration/pipelines/robot-execution.Jenkinsfile'

folder(jobFolder) {
    description('Robot executor jobs managed from jenkins-integration/jobs.')
}

pipelineJob(jobName) {
    description(
        'Robot execution entry backed by jenkins-integration/pipelines/robot-execution.Jenkinsfile. ' +
        'Default repo URLs and credentials come from JCasC/global env, while refs stay job-level configurable.'
    )

    parameters {
        textParam('RUN_REQUEST_JSON', '', 'Preferred internal robot request JSON for CI/CD triggers and future platform-api handoff.')
        stringParam('RUN_ID', '', 'platform-api created run_id. Optional for local smoke.')
        stringParam('TESTLINE', '7_5_UTE5G402T813', 'Target testline used by Robot variable file resolution.')
        stringParam('ROBOTCASE_PATH', 'testsuite/Hangzhou/RRM/example.robot', 'Robot case path, relative to workspace root or robotws root.')
        stringParam('CASE_NAME', '', 'Optional Robot test case name passed with -t.')
        textParam('ROBOT_SELECTED_TESTS', '', 'Optional newline-separated Robot test names. Mirrors repeated -t usage in the legacy pipeline.')
        textParam('ROBOT_VARIABLES_JSON', '{}', 'Optional Robot variable mapping, for example {"AF_PATH":"...","target_version":"..."}.')
        stringParam('PYTHON_ENV_ROOT', '', 'Optional Python environment root. Defaults to /home/ute/CIENV/<TESTLINE>.')
        stringParam('ROBOTWS_ROOT', '', 'Optional explicit robotws root. Useful when workspace layout differs from repo root.')
        stringParam('TESTLINE_VARIABLES_PATH', '', 'Optional explicit testline variable path. Defaults to testline_configuration/<TESTLINE>.')
        stringParam('ROBOTWS_REPO_URL_OVERRIDE', '', 'Optional robotws repo URL override. Default source should come from Jenkins global env / JCasC ROBOTWS_REPO_URL.')
        stringParam('ROBOTWS_GIT_REF', 'master', 'robotws branch/tag/commit. Job-level configurable, current default is master.')
        stringParam('ROBOTWS_CREDENTIALS_ID_OVERRIDE', '', 'Optional robotws credentials override. Default source should come from Jenkins global env / JCasC ROBOTWS_CREDENTIALS_ID.')
        stringParam('TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE', '', 'Optional testline_configuration repo URL override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_REPO_URL.')
        stringParam('TESTLINE_CONFIGURATION_GIT_REF', 'master', 'testline_configuration branch/tag/commit. Job-level configurable, current default is master.')
        stringParam('TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE', '', 'Optional testline_configuration credentials override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_CREDENTIALS_ID.')
        stringParam('ARTIFACT_LABEL', 'quicktest', 'Artifact label segment used in artifact/<label>/retry-<n>/<suite>.')
        stringParam('RETRY_INDEX', '0', 'Retry index used in artifact directory naming.')
        stringParam('ROBOT_LOG_LEVEL', 'TRACE', 'Robot log level passed with -L.')
        stringParam('PLATFORM_API_BASE_URL', '', 'Optional platform-api base URL used by the callback stage later.')
        stringParam('CALLBACK_MAX_ATTEMPTS', '3', 'Maximum callback retry attempts sent by post_run_callback.py.')
        stringParam('CALLBACK_BACKOFF_SECONDS', '2', 'Linear backoff base seconds between callback retries.')
        booleanParam('CALLBACK_IGNORE_FAILURE', true, 'Do not fail the pipeline if callback sending still fails after retries.')
    }

    definition {
        cps {
            script(readFileFromWorkspace(pipelinePath))
            sandbox(true)
        }
    }
}