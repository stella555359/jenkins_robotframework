pipeline {
    agent any

    environment {
        ROBOT_REQUEST_PATH = 'artifacts/robot-request.json'
        CHECKOUT_PLAN_PATH = 'artifacts/source-checkout.json'
        PYTHON_ENV_PLAN_PATH = 'artifacts/python-env.json'
        ROBOT_COMMAND_PLAN_PATH = 'artifacts/robot-command.json'
        CALLBACK_PAYLOAD_PATH = 'artifacts/callback-payload.json'
        CALLBACK_FALLBACK_PATH = 'artifacts/callback-fallback.json'
        CALLBACK_SEND_RESULT_PATH = 'artifacts/callback-send-result.json'
    }

    parameters {
        text(name: 'RUN_REQUEST_JSON', defaultValue: '', description: 'Preferred internal robot request JSON for CI/CD triggers and future platform-api handoff.')
        string(name: 'RUN_ID', defaultValue: '', description: 'platform-api created run_id. Optional for local smoke.')
        string(name: 'TESTLINE', defaultValue: '7_5_UTE5G402T813', description: 'Target testline used by Robot variable file resolution.')
        string(name: 'ROBOTCASE_PATH', defaultValue: 'testsuite/Hangzhou/RRM/example.robot', description: 'Robot case path, relative to workspace root or robotws root.')
        string(name: 'CASE_NAME', defaultValue: '', description: 'Optional Robot test case name passed with -t.')
        text(name: 'ROBOT_SELECTED_TESTS', defaultValue: '', description: 'Optional newline-separated Robot test names. Mirrors repeated -t usage in the legacy pipeline.')
        text(name: 'ROBOT_VARIABLES_JSON', defaultValue: '{}', description: 'Optional Robot variable mapping, for example {"AF_PATH":"...","target_version":"..."}.')
        string(name: 'PYTHON_ENV_ROOT', defaultValue: '', description: 'Optional Python environment root. Defaults to /home/ute/CIENV/<TESTLINE>.')
        string(name: 'ROBOTWS_ROOT', defaultValue: '', description: 'Optional explicit robotws root. Useful when workspace layout differs from repo root.')
        string(name: 'TESTLINE_VARIABLES_PATH', defaultValue: '', description: 'Optional explicit testline variable path. Defaults to testline_configuration/<TESTLINE>.')
        string(name: 'ROBOTWS_REPO_URL_OVERRIDE', defaultValue: '', description: 'Optional robotws repo URL override. Default source should come from Jenkins global env / JCasC ROBOTWS_REPO_URL.')
        string(name: 'ROBOTWS_GIT_REF', defaultValue: 'master', description: 'robotws branch/tag/commit. Job-level configurable, current default is master.')
        string(name: 'ROBOTWS_CREDENTIALS_ID_OVERRIDE', defaultValue: '', description: 'Optional robotws credentials override. Default source should come from Jenkins global env / JCasC ROBOTWS_CREDENTIALS_ID.')
        string(name: 'TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE', defaultValue: '', description: 'Optional testline_configuration repo URL override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_REPO_URL.')
        string(name: 'TESTLINE_CONFIGURATION_GIT_REF', defaultValue: 'master', description: 'testline_configuration branch/tag/commit. Job-level configurable, current default is master.')
        string(name: 'TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE', defaultValue: '', description: 'Optional testline_configuration credentials override. Default source should come from Jenkins global env / JCasC TESTLINE_CONFIGURATION_CREDENTIALS_ID.')
        string(name: 'ARTIFACT_LABEL', defaultValue: 'quicktest', description: 'Artifact label segment used in artifact/<label>/retry-<n>/<suite>.')
        string(name: 'RETRY_INDEX', defaultValue: '0', description: 'Retry index used in artifact directory naming.')
        string(name: 'ROBOT_LOG_LEVEL', defaultValue: 'TRACE', description: 'Robot log level passed with -L.')
        string(name: 'PLATFORM_API_BASE_URL', defaultValue: '', description: 'Optional platform-api base URL used by the callback stage later.')
        string(name: 'CALLBACK_MAX_ATTEMPTS', defaultValue: '3', description: 'Maximum callback retry attempts sent by post_run_callback.py.')
        string(name: 'CALLBACK_BACKOFF_SECONDS', defaultValue: '2', description: 'Linear backoff base seconds between callback retries.')
        booleanParam(name: 'CALLBACK_IGNORE_FAILURE', defaultValue: true, description: 'Do not fail the pipeline if callback sending still fails after retries.')
    }

    stages {
        stage('Materialize Run Request') {
            steps {
                sh 'mkdir -p artifacts'
                script {
                    env.CALLBACK_RUN_ID = params.RUN_ID?.trim() ?: ''
                    env.RUN_STARTED_AT = new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX", TimeZone.getTimeZone('Asia/Shanghai'))
                    if (params.RUN_REQUEST_JSON?.trim()) {
                        writeFile(file: 'artifacts/run-request-source.json', text: params.RUN_REQUEST_JSON)
                    } else {
                        def selectedTests = params.ROBOT_SELECTED_TESTS
                            .readLines()
                            .collect { it.trim() }
                            .findAll { it }
                        def variables = params.ROBOT_VARIABLES_JSON?.trim()
                            ? new groovy.json.JsonSlurperClassic().parseText(params.ROBOT_VARIABLES_JSON)
                            : [:]
                        def requestPayload = [
                            run_id: params.RUN_ID?.trim(),
                            executor_type: 'robot',
                            testline: params.TESTLINE?.trim(),
                            robotcase_path: params.ROBOTCASE_PATH?.trim(),
                            robotws_root: params.ROBOTWS_ROOT?.trim(),
                            testline_variables_path: params.TESTLINE_VARIABLES_PATH?.trim(),
                            metadata: [
                                case_name: params.CASE_NAME?.trim(),
                                selected_tests: selectedTests,
                                robot_variables: variables,
                                artifact_label: params.ARTIFACT_LABEL?.trim(),
                                retry_index: params.RETRY_INDEX?.trim(),
                                log_level: params.ROBOT_LOG_LEVEL?.trim(),
                                python_env_root: params.PYTHON_ENV_ROOT?.trim() ?: "/home/ute/CIENV/${params.TESTLINE?.trim()}",
                                robotws_repo_url: params.ROBOTWS_REPO_URL_OVERRIDE?.trim(),
                                robotws_ref: params.ROBOTWS_GIT_REF?.trim(),
                                robotws_credentials_id: params.ROBOTWS_CREDENTIALS_ID_OVERRIDE?.trim(),
                                testline_configuration_repo_url: params.TESTLINE_CONFIGURATION_REPO_URL_OVERRIDE?.trim(),
                                testline_configuration_ref: params.TESTLINE_CONFIGURATION_GIT_REF?.trim(),
                                testline_configuration_credentials_id: params.TESTLINE_CONFIGURATION_CREDENTIALS_ID_OVERRIDE?.trim(),
                            ].findAll { entry ->
                                def value = entry.value
                                if (value == null) {
                                    return false
                                }
                                if (value instanceof String) {
                                    return value.trim()
                                }
                                if (value instanceof Collection) {
                                    return !value.isEmpty()
                                }
                                if (value instanceof Map) {
                                    return !value.isEmpty()
                                }
                                return true
                            },
                        ]
                        writeFile(
                            file: 'artifacts/run-request-source.json',
                            text: groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(requestPayload)),
                        )
                    }
                }
                script {
                    if (!params.RUN_REQUEST_JSON?.trim() && params.RUN_ID?.trim() && params.PLATFORM_API_BASE_URL?.trim()) {
                        sh '''
                            python jenkins-integration/scripts/materialize_run_request.py \
                              --run-id "$RUN_ID" \
                              --platform-api-base-url "$PLATFORM_API_BASE_URL" \
                              --workspace-root "$WORKSPACE" \
                              --output-json "$WORKSPACE/$ROBOT_REQUEST_PATH"
                        '''
                    } else {
                        sh '''
                            python jenkins-integration/scripts/materialize_run_request.py \
                              --input-json "$WORKSPACE/artifacts/run-request-source.json" \
                              --platform-api-base-url "$PLATFORM_API_BASE_URL" \
                              --workspace-root "$WORKSPACE" \
                              --output-json "$WORKSPACE/$ROBOT_REQUEST_PATH"
                        '''
                    }

                    def materializedRequest = new groovy.json.JsonSlurperClassic().parseText(readFile(env.ROBOT_REQUEST_PATH))
                    env.CALLBACK_RUN_ID = materializedRequest.run_id?.toString()?.trim() ?: env.CALLBACK_RUN_ID
                }
            }
        }

        stage('Prepare Workspace') {
            steps {
                sh '''
                    python jenkins-integration/scripts/checkout_sources.py \
                      --request-json "$WORKSPACE/$ROBOT_REQUEST_PATH" \
                      --workspace-root "$WORKSPACE" \
                      --output-json "$WORKSPACE/$CHECKOUT_PLAN_PATH" \
                      --shell-script-output "$WORKSPACE/artifacts/checkout-sources.sh"

                    python jenkins-integration/scripts/prepare_taf_environment.py \
                      --request-json "$WORKSPACE/$ROBOT_REQUEST_PATH" \
                      --output-json "$WORKSPACE/$PYTHON_ENV_PLAN_PATH" \
                      --shell-script-output "$WORKSPACE/artifacts/prepare-python-env.sh"
                '''
                script {
                    def checkoutPlan = new groovy.json.JsonSlurperClassic().parseText(readFile(env.CHECKOUT_PLAN_PATH))
                    def credentialIds = checkoutPlan.operations
                        .collect { operation ->
                            def explicitCredentialId = operation.credentials_id?.toString()?.trim()
                            if (explicitCredentialId) {
                                return explicitCredentialId
                            }
                            def envName = operation.credentials_id_env?.toString()?.trim()
                            return envName ? env[envName]?.trim() : ''
                        }
                        .findAll { it }
                        .unique()

                    if (credentialIds) {
                        sshagent(credentials: credentialIds) {
                            sh 'bash "$WORKSPACE/artifacts/checkout-sources.sh"'
                        }
                    } else {
                        sh 'bash "$WORKSPACE/artifacts/checkout-sources.sh"'
                    }
                }
                sh 'bash "$WORKSPACE/artifacts/prepare-python-env.sh"'
            }
        }

        stage('Build Robot Command') {
            steps {
                sh '''
                    python jenkins-integration/scripts/build_robot_command.py \
                      --request-json "$WORKSPACE/$ROBOT_REQUEST_PATH" \
                      --workspace-root "$WORKSPACE" \
                      --output-json "$WORKSPACE/$ROBOT_COMMAND_PLAN_PATH"
                '''
            }
        }

        stage('Run Robot Case') {
            steps {
                sh '''
                    python - <<'PY'
import json
from pathlib import Path

plan = json.loads(Path('artifacts/robot-command.json').read_text(encoding='utf-8'))
script_path = Path('artifacts/run-robot.sh')
script_path.write_text(plan['shell']['shell_script_text'], encoding='utf-8')
print(plan['shell']['shell_script_text'])
PY
                    bash artifacts/run-robot.sh
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true
            script {
                def finishedAt = new Date().format("yyyy-MM-dd'T'HH:mm:ssXXX", TimeZone.getTimeZone('Asia/Shanghai'))
                def callbackStatus = currentBuild.currentResult == 'SUCCESS' ? 'passed' : 'failed'
                def callbackMessage = currentBuild.currentResult == 'SUCCESS' ? 'Robot execution completed.' : 'Robot execution failed. See Jenkins artifacts.'
                if (env.CALLBACK_RUN_ID?.trim() && params.PLATFORM_API_BASE_URL?.trim()) {
                    def callbackArgs = [
                        'python jenkins-integration/scripts/post_run_callback.py',
                        "  --run-id \"${env.CALLBACK_RUN_ID}\"",
                        "  --status \"${callbackStatus}\"",
                        "  --message \"${callbackMessage}\"",
                        "  --jenkins-build-ref \"${JOB_NAME}#${BUILD_NUMBER}\"",
                        "  --started-at \"${RUN_STARTED_AT}\"",
                        "  --finished-at \"${finishedAt}\"",
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
                    callbackArgs.add('  --output-json "$WORKSPACE/$CALLBACK_PAYLOAD_PATH"')
                    sh callbackArgs.join(' \\\n')
                }
            }
        }
    }
}
