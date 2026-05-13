import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.common.StandardUsernameCredentials
import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey
import jenkins.model.Jenkins

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path


def credentialIds = ["robotws-ssh", "testline-config-ssh"]
def jenkins = Jenkins.get()
def credentials = CredentialsProvider.lookupCredentials(
    StandardUsernameCredentials.class,
    jenkins,
    null,
    null,
)

def runCommand = { List<String> command ->
    def process = new ProcessBuilder(command)
        .redirectErrorStream(true)
        .start()
    def output = process.inputStream.getText("UTF-8").trim()
    def exitCode = process.waitFor()
    [exitCode: exitCode, output: output]
}

credentialIds.each { credentialId ->
    println("=== ${credentialId} ===")
    def credential = credentials.find { it.id == credentialId }
    if (!(credential instanceof BasicSSHUserPrivateKey)) {
        println("Credential not found or not an SSH private key credential.")
        println()
        return
    }

    println("username: ${credential.username}")
    Path tempFile = Files.createTempFile("jenkins-ssh-credential-", ".key")
    try {
        Files.writeString(tempFile, credential.privateKey + System.lineSeparator(), StandardCharsets.UTF_8)
        tempFile.toFile().setReadable(false, false)
        tempFile.toFile().setReadable(true, true)
        tempFile.toFile().setWritable(true, true)

        def publicKey = runCommand(["/usr/bin/ssh-keygen", "-y", "-f", tempFile.toString()])
        def fingerprint = runCommand(["/usr/bin/ssh-keygen", "-lf", tempFile.toString()])

        if (publicKey.exitCode == 0) {
            println("public key:")
            println(publicKey.output)
        } else {
            println("public key extraction failed:")
            println(publicKey.output)
        }

        if (fingerprint.exitCode == 0) {
            println("fingerprint:")
            println(fingerprint.output)
        } else {
            println("fingerprint extraction failed:")
            println(fingerprint.output)
        }
    } finally {
        Files.deleteIfExists(tempFile)
    }
    println()
}