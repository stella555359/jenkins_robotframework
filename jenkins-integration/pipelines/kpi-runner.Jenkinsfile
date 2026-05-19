pipeline {
    agent { label 't813 && robot' }

    environment {
        RUNNER_REQUEST_PATH = 'artifacts/python-orchestrator-request.json'
        CHECKOUT_PLAN_PATH = 'artifacts/source-checkout.json'
        PYTHON_ENV_PLAN_PATH = 'artifacts/python-env.json'
        RESULT_JSON_DEFAULT_PATH = 'artifacts/python-kpi-runner-result.json'
        CALLBACK_PAYLOAD_PATH = 'artifacts/callback-payload.json'
        CALLBACK_FALLBACK_PATH = 'artifacts/callback-fallback.json'
        CALLBACK_SEND_RESULT_PATH = 'artifacts/callback-send-result.json'
        RUNNER_METADATA_PATH = 'artifacts/python-kpi-runner-metadata.json'
    }

    parameters {
        text(name: 'RUN_REQUEST_JSON', defaultValue: '', description: 'Optional full python_orchestrator run detail or runner request JSON. RUN_ID + PLATFORM_API_BASE_URL is preferred for platform-api triggers.')
        string(name: 'RUN_ID', defaultValue: '', description: 'platform-api created run_id. Optional for local smoke.')
        string(name: 'TESTLINE', defaultValue: '7_5_UTE5G402T813', description: 'Target testline used by runner config resolution.')
        string(name: 'WORKFLOW_NAME', defaultValue: 'Python KPI Runner', description: 'Human-readable workflow name used in request metadata and build display names.')
        text(name: 'WORKFLOW_SPEC_JSON', defaultValue: '{}', description: 'WorkflowSpec JSON created by platform-api / automation-portal.')
        string(name: 'BUILD', defaultValue: '', description: 'CIT package / software build under test, for example SBTS26R1.ENB.9999.')
        booleanParam(name: 'DRY_RUN', defaultValue: true, description: 'Run without loading real env_map or TAF bindings.')
        string(name: 'RUNNER_REPOSITORY_ROOT', defaultValue: '', description: 'Optional test-workflow-runner repository root. Defaults to $WORKSPACE/test-workflow-runner.')
        string(name: 'RESULT_JSON_PATH', defaultValue: '', description: 'Optional result JSON path. Defaults to artifacts/python-kpi-runner-result.json.')
        choice(name: 'TAF_MODE', choices: ['reuse', 'create-venv', 'skip-install'], description: 'TAF/python environment mode. reuse expects an existing CIENV, create-venv creates a new CIENV and installs TAF dependencies from robotws, skip-install only skips package installation.')
        string(name: 'PYTHON_ENV_ROOT', defaultValue: '', description: 'Optional Python environment root. Defaults to /home/ute/CIENV/<TESTLINE>.')
        string(name: 'PIP_INDEX_URL_OVERRIDE', defaultValue: '', description: 'Optional pip index URL override for create-venv installs. Falls back to Jenkins global env PIP_INDEX_URL.')
        string(name: 'PIP_EXTRA_INDEX_URL_OVERRIDE', defaultValue: '', description: 'Optional fallback pip index URL override for create-venv installs. Used when PIP_INDEX_URL_OVERRIDE and Jenkins global PIP_INDEX_URL are empty.')
        string(name: 'PIP_TRUSTED_HOST_OVERRIDE', defaultValue: '', description: 'Optional pip trusted-host override for create-venv installs. Falls back to Jenkins global env PIP_TRUSTED_HOST.')
        string(name: 'ROBOTWS_ROOT', defaultValue: '', description: 'Optional explicit robotws root. Useful when workspace layout differs from repo root.')
        string(name: 'TESTLINE_VARIABLES_PATH', defaultValue: '', description: 'Optional explicit testline variable path. Defaults to testline_configuration/<TESTLINE>.')
        string(name: 'ROBOTWS_REPO_URL_OVERRIDE', defaultValue: '', description: 'Optional robotws repo URL override. Default source should come from Jenkins global env / JCasC ROBOTWS_REPO_URL.')
        string(name: 'ROBOTWS_GIT_REF', defaultValue: 'master', description: 'robotws branch/tag/commit. Job-level configurable, current default is master.')
        string(name: 'ROBOTWS_CREDENTIALS_ID_OVERRIDE', defaultValue: '', description: 'Optional robotws credentials override. Default source should come from Jenkins global env / JCasC ROBOTWS_CREDENTIALS_ID.')
        string(name: 'TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE', defaultValue: '', description: 'Optional testline_configuration repo URL override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_REPO_URL.')
        string(name: 'TESTLINE_CONFIGURATION_GIT_REF', defaultValue: 'master', description: 'testline_configuration branch/tag/commit. Job-level configurable, current default is master.')
        string(name: 'TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE', defaultValue: '', description: 'Optional testline_configuration credentials override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_CREDENTIALS_ID.')
        string(name: 'ARTIFACT_LABEL', defaultValue: 'kpi-runner', description: 'Artifact label segment used in request metadata and archive organization.')
        string(name: 'RETRY_INDEX', defaultValue: '0', description: 'Retry index used in artifact directory naming.')
        string(name: 'PLATFORM_API_BASE_URL', defaultValue: '', description: 'Optional platform-api base URL used by request fetch and callback.')
        string(name: 'CALLBACK_MAX_ATTEMPTS', defaultValue: '3', description: 'Maximum callback retry attempts sent by post_run_callback.py.')
        string(name: 'CALLBACK_BACKOFF_SECONDS', defaultValue: '2', description: 'Linear backoff base seconds between callback retries.')
        booleanParam(name: 'CALLBACK_IGNORE_FAILURE', defaultValue: true, description: 'Do not fail the pipeline if callback sending still fails after retries.')
        booleanParam(name: 'CALLBACK_INSECURE_TLS', defaultValue: true, description: 'Skip TLS certificate verification for platform-api callback. Keep enabled when Nginx HTTPS uses a self-signed certificate.')
    }

    stages {
        stage('Checkout Pipeline Source') {
            steps {
                script {
                    def repositoryUrl = env.JENKINS_ROBOTFRAMEWORK_REPO_URL?.trim()
                    if (!repositoryUrl || repositoryUrl.startsWith('${')) {
                        repositoryUrl = 'https://github.com/stella555359/jenkins_robotframework.git'
                    }

                    def repositoryRef = env.JENKINS_ROBOTFRAMEWORK_GIT_REF?.trim()
                    if (!repositoryRef || repositoryRef.startsWith('${')) {
                        repositoryRef = 'main'
                    }

                    def credentialsId = env.JENKINS_ROBOTFRAMEWORK_CREDENTIALS_ID?.trim()
                    if (credentialsId?.startsWith('${')) {
                        credentialsId = ''
                    }

                    def checkoutArgs = [
                        url: repositoryUrl,
                        branch: repositoryRef,
                    ]
                    if (credentialsId) {
                        checkoutArgs.credentialsId = credentialsId
                    }

                    deleteDir()
                    git checkoutArgs
                }
            }
        }

        stage('Materialize Workflow Request') {
            steps {
                sh 'mkdir -p artifacts'
                script {
                    env.CALLBACK_RUN_ID = params.RUN_ID?.trim() ?: ''
                    env.RUN_STARTED_AT = new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX", TimeZone.getTimeZone('Asia/Shanghai'))
                    env.RUNNER_RESULT_JSON_PATH = params.RESULT_JSON_PATH?.trim() ?: env.RESULT_JSON_DEFAULT_PATH
                    env.RUNNER_REPO_ROOT = params.RUNNER_REPOSITORY_ROOT?.trim() ?: "${env.WORKSPACE}/test-workflow-runner"
                    currentBuild.displayName = "#${BUILD_NUMBER} ${params.TESTLINE} ${params.BUILD?.trim() ?: 'no-build'} ${params.DRY_RUN ? 'dryrun' : 'realrun'}"

                    writeFile(file: 'artifacts/notify-stage.sh', text: '''\
#!/bin/bash
# Usage: bash artifacts/notify-stage.sh <stage_name> <stage_status> [message]
STAGE_NAME="$1"
STAGE_STATUS="$2"
STAGE_MESSAGE="${3:-}"
RUN_ID="${CALLBACK_RUN_ID:-}"
API_BASE="${PLATFORM_API_BASE_URL:-}"
INSECURE="${CALLBACK_INSECURE_TLS:-false}"

if [ -z "$RUN_ID" ] || [ -z "$API_BASE" ]; then
    echo "[notify-stage] Skipped: RUN_ID or PLATFORM_API_BASE_URL not set."
    exit 0
fi

CURL_OPTS="-s -o /dev/null -w %{http_code} --max-time 5"
if [ "$INSECURE" = "true" ]; then
    CURL_OPTS="$CURL_OPTS -k"
fi

PAYLOAD="{\\"stage_name\\": \\"${STAGE_NAME}\\", \\"stage_status\\": \\"${STAGE_STATUS}\\"}"
if [ -n "$STAGE_MESSAGE" ]; then
    PAYLOAD="{\\"stage_name\\": \\"${STAGE_NAME}\\", \\"stage_status\\": \\"${STAGE_STATUS}\\", \\"message\\": \\"${STAGE_MESSAGE}\\"}"
fi

HTTP_CODE=$(curl $CURL_OPTS -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "${API_BASE}/api/runs/${RUN_ID}/stages" 2>/dev/null || echo "000")
echo "[notify-stage] ${STAGE_NAME} -> ${STAGE_STATUS} (HTTP ${HTTP_CODE})"
''')
                    sh 'chmod +x artifacts/notify-stage.sh'
                }
                sh 'bash artifacts/notify-stage.sh "Materialize Workflow Request" started'
                script {
                    def materializeArgs = [
                        'python3 jenkins-integration/scripts/materialize_python_orchestrator_request.py',
                        '  --testline "$TESTLINE"',
                        '  --workflow-name "$WORKFLOW_NAME"',
                        '  --workflow-spec-json "$WORKFLOW_SPEC_JSON"',
                        '  --build "$BUILD"',
                        '  --workspace-root "$WORKSPACE"',
                        '  --python-env-root "$PYTHON_ENV_ROOT"',
                        '  --taf-mode "$TAF_MODE"',
                        '  --robotws-root "$ROBOTWS_ROOT"',
                        '  --testline-variables-path "$TESTLINE_VARIABLES_PATH"',
                        '  --runner-repository-root "$RUNNER_REPO_ROOT"',
                        '  --result-json-path "$WORKSPACE/$RUNNER_RESULT_JSON_PATH"',
                        '  --artifact-label "$ARTIFACT_LABEL"',
                        '  --retry-index "$RETRY_INDEX"',
                        '  --output-json "$WORKSPACE/$RUNNER_REQUEST_PATH"',
                    ]
                    if (params.RUN_REQUEST_JSON?.trim()) {
                        writeFile(file: 'artifacts/run-request-source.json', text: params.RUN_REQUEST_JSON)
                        materializeArgs.add('  --input-json "$WORKSPACE/artifacts/run-request-source.json"')
                    } else if (params.RUN_ID?.trim() && params.PLATFORM_API_BASE_URL?.trim()) {
                        materializeArgs.add('  --run-id "$RUN_ID"')
                        materializeArgs.add('  --platform-api-base-url "$PLATFORM_API_BASE_URL"')
                    }
                    if (params.DRY_RUN) {
                        materializeArgs.add('  --dry-run')
                    }
                    if (params.CALLBACK_INSECURE_TLS) {
                        materializeArgs.add('  --insecure-skip-tls-verify')
                    }
                    sh materializeArgs.join(' \\\n')
                }
                sh '''
                    python3 - <<'PY'
import json
from pathlib import Path

request = json.loads(Path('artifacts/python-orchestrator-request.json').read_text(encoding='utf-8'))
Path('artifacts/callback-run-id.txt').write_text(str(request.get('run_id') or ''), encoding='utf-8')
PY
                '''
                script {
                    def callbackRunId = readFile('artifacts/callback-run-id.txt').trim()
                    env.CALLBACK_RUN_ID = callbackRunId ?: env.CALLBACK_RUN_ID
                }
                sh 'bash artifacts/notify-stage.sh "Materialize Workflow Request" completed'
            }
        }

        stage('Prepare Workspace') {
            steps {
                sh 'bash artifacts/notify-stage.sh "Prepare Workspace" started'
                sh '''
                    python3 jenkins-integration/scripts/checkout_sources.py \
                      --request-json "$WORKSPACE/$RUNNER_REQUEST_PATH" \
                      --workspace-root "$WORKSPACE" \
                      --output-json "$WORKSPACE/$CHECKOUT_PLAN_PATH" \
                      --shell-script-output "$WORKSPACE/artifacts/checkout-sources.sh"

                    python3 jenkins-integration/scripts/prepare_taf_environment.py \
                      --request-json "$WORKSPACE/$RUNNER_REQUEST_PATH" \
                      --output-json "$WORKSPACE/$PYTHON_ENV_PLAN_PATH" \
                      --shell-script-output "$WORKSPACE/artifacts/prepare-python-env.sh"
                '''
                script {
                    sh '''
                        python3 - <<'PY'
import json
import os
from pathlib import Path

plan = json.loads(Path('artifacts/source-checkout.json').read_text(encoding='utf-8'))
credential_ids = []

for operation in plan.get('operations', []):
    credential_kind = str(operation.get('credential_kind') or '').strip()
    if credential_kind and credential_kind != 'sshagent':
        continue

    explicit_credential_id = str(operation.get('credentials_id') or '').strip()
    if explicit_credential_id:
        credential_ids.append(explicit_credential_id)
        continue

    env_name = str(operation.get('credentials_id_env') or '').strip()
    resolved_credential_id = os.environ.get(env_name, '').strip() if env_name else ''
    if resolved_credential_id:
        credential_ids.append(resolved_credential_id)

unique_credential_ids = list(dict.fromkeys(credential_ids))
Path('artifacts/checkout-credential-ids.txt').write_text(
    '\\n'.join(unique_credential_ids),
    encoding='utf-8',
)
PY
                    '''

                    def credentialIds = readFile('artifacts/checkout-credential-ids.txt')
                        .readLines()
                        .collect { it.trim() }
                        .findAll { it }

                    if (credentialIds) {
                        sshagent(credentials: credentialIds) {
                            sh 'bash "$WORKSPACE/artifacts/checkout-sources.sh"'
                        }
                    } else {
                        sh 'bash "$WORKSPACE/artifacts/checkout-sources.sh"'
                    }
                }
                sh 'bash "$WORKSPACE/artifacts/prepare-python-env.sh"'
                sh 'bash artifacts/notify-stage.sh "Prepare Workspace" completed'
            }
        }

        stage('Run Test Workflow Runner') {
            steps {
                sh 'bash artifacts/notify-stage.sh "Run Test Workflow Runner" started'
                script {
                    def runnerArgs = [
                        'set -euo pipefail',
                        'PYTHON_ENV_ACTIVATE=$(python3 - <<\'PY\'',
                        'import json',
                        'from pathlib import Path',
                        'plan = json.loads(Path("artifacts/python-env.json").read_text(encoding="utf-8"))',
                        'print(plan.get("activate_script") or "")',
                        'PY',
                        ')',
                        'if [ -n "$PYTHON_ENV_ACTIVATE" ] && [ -f "$PYTHON_ENV_ACTIVATE" ]; then . "$PYTHON_ENV_ACTIVATE"; fi',
                        'export PYTHONPATH="$WORKSPACE/test-workflow-runner:$WORKSPACE/robotws:$WORKSPACE/testline_configuration:${PYTHONPATH:-}"',
                        'python -m test_workflow_runner.cli "$WORKSPACE/$RUNNER_REQUEST_PATH" --result-json "$WORKSPACE/$RUNNER_RESULT_JSON_PATH" --repository-root "$RUNNER_REPO_ROOT"',
                    ]
                    if (params.DRY_RUN) {
                        runnerArgs[-1] = runnerArgs[-1] + ' --dry-run'
                    }
                    writeFile(file: 'artifacts/run-test-workflow-runner.sh', text: runnerArgs.join('\n') + '\n')
                    sh 'chmod +x artifacts/run-test-workflow-runner.sh'
                    sh 'bash artifacts/run-test-workflow-runner.sh'
                }
                sh 'bash artifacts/notify-stage.sh "Run Test Workflow Runner" completed'
            }
        }

        stage('Collect Runner Metadata') {
            steps {
                sh 'bash artifacts/notify-stage.sh "Collect Runner Metadata" started'
                sh '''
                    python3 - <<'PY'
import json
import os
from pathlib import Path

result_path = Path(os.environ.get('RUNNER_RESULT_JSON_PATH', 'artifacts/python-kpi-runner-result.json'))
if not result_path.is_absolute():
    result_path = Path(os.environ['WORKSPACE']) / result_path

result_payload = {}
if result_path.exists():
    result_payload = json.loads(result_path.read_text(encoding='utf-8'))

metadata = {
    'runner_request_path': str(Path(os.environ['WORKSPACE']) / os.environ['RUNNER_REQUEST_PATH']),
    'runner_result_path': str(result_path),
    'runner_result': result_payload,
    'workflow_name': os.environ.get('WORKFLOW_NAME', ''),
    'build': os.environ.get('BUILD', ''),
    'dry_run': os.environ.get('DRY_RUN', ''),
}
Path(os.environ['RUNNER_METADATA_PATH']).write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2),
    encoding='utf-8',
)
PY
                '''
                sh 'bash artifacts/notify-stage.sh "Collect Runner Metadata" completed'
            }
        }
    }

    post {
        always {
            sh 'bash artifacts/notify-stage.sh "Callback" started || true'
            archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true
            script {
                def finishedAt = new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX", TimeZone.getTimeZone('Asia/Shanghai'))
                def callbackStatus = currentBuild.currentResult == 'SUCCESS' ? 'passed' : 'failed'
                def callbackMessage = currentBuild.currentResult == 'SUCCESS' ? 'Python KPI Runner completed.' : 'Python KPI Runner failed. See Jenkins artifacts.'
                if (env.CALLBACK_RUN_ID?.trim() && params.PLATFORM_API_BASE_URL?.trim()) {
                    def callbackArgs = [
                        'python3 jenkins-integration/scripts/post_run_callback.py',
                        "  --run-id \"${env.CALLBACK_RUN_ID}\"",
                        "  --status \"${callbackStatus}\"",
                        "  --message \"${callbackMessage}\"",
                        "  --jenkins-build-ref \"${JOB_NAME}#${BUILD_NUMBER}\"",
                        "  --started-at \"${RUN_STARTED_AT}\"",
                        "  --finished-at \"${finishedAt}\"",
                        '  --metadata-json "$WORKSPACE/$RUNNER_METADATA_PATH"',
                        '  --artifact-dir "$WORKSPACE/artifacts"',
                        '  --platform-api-base-url "$PLATFORM_API_BASE_URL"',
                        '  --max-attempts "$CALLBACK_MAX_ATTEMPTS"',
                        '  --backoff-seconds "$CALLBACK_BACKOFF_SECONDS"',
                        '  --fallback-output-json "$WORKSPACE/$CALLBACK_FALLBACK_PATH"',
                        '  --send-result-json "$WORKSPACE/$CALLBACK_SEND_RESULT_PATH"',
                    ]
                    if (params.CALLBACK_IGNORE_FAILURE) {
                        callbackArgs.add('  --ignore-send-failure')
                    }
                    if (params.CALLBACK_INSECURE_TLS) {
                        callbackArgs.add('  --insecure-skip-tls-verify')
                    }
                    callbackArgs.add('  --output-json "$WORKSPACE/$CALLBACK_PAYLOAD_PATH"')
                    sh callbackArgs.join(' \\\n')
                    sh 'bash artifacts/notify-stage.sh "Callback" completed || true'
                }
            }
        }
    }
}
