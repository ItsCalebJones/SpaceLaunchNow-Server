#!/usr/bin/env groovy

def defineImageName() {
    def branchName = "${env.BRANCH_NAME}"
    branchName = branchName.replace ('/', '_')
    branchName = branchName.replace ('.', '')
    return "${branchName}-b${BUILD_NUMBER}"
}
def commitMessage() {
    def message = sh(returnStdout: true, script: "git log --format='medium' -1 ${GIT_COMMIT}").trim()
    return "${message}"
}

def projectName() {
  def jobNameParts = env.JOB_NAME.tokenize('/') as String[]
  return jobNameParts.length < 2 ? env.JOB_NAME : jobNameParts[jobNameParts.length - 2]
}

pipeline{
	agent any
	
	environment {
		BRANCH = "${BRANCH_NAME}"
		registry="registry.calebjones.dev:5050/sln-server"
		registryURL = "https://registry.calebjones.dev:5050/sln-server"
		registryCredential = 'calebregistry'
		imageName = defineImageName()
		dockerImage = ''
        DISCORD_URL = credentials('DiscordURL')
        COMMIT_MESSAGE = commitMessage()
        PROJECT_NAME = projectName()
	}
	
	stages{
		stage('Setup'){
			steps {
				withCredentials([file(credentialsId: 'SLNTestConfig', variable: 'configFile')]) {
					sh 'cp $configFile spacelaunchnow/config.py'
				}
				sh 'mkdir -p log'
				sh 'touch log/daily_digest.log'
				sshagent (credentials: ['SLN_Builds']) {
                        withPythonEnv('python3') {
                        sh 'python3 -m pip install -r requirements.txt'
                    }
                }
			}
		}

		stage('Build Docker Image'){
			steps{
				script{
                    if (env.BRANCH_NAME == 'master') {
                        withCredentials([file(credentialsId: 'SLNProductionConfig', variable: 'configFile')]) {
                            sh 'cp $configFile spacelaunchnow/config.py'
                        }
                    } else {
                        withCredentials([file(credentialsId: 'SLNConfig', variable: 'configFile')]) {
                            sh 'cp $configFile spacelaunchnow/config.py'
                        }
                    }
					if(!fileExists("Dockerfile")){
						echo "No Dockerfile";
					}else{

					withCredentials([string(credentialsId: 'SSH_KEY_SLN', variable: 'TOKEN')]) {
					    def dockerReg = registry + ":" + imageName
					    println(TOKEN)
						dockerImage = docker.build(dockerReg, '--build-arg SSH_PRIVATE_KEY="$TOKEN" .')
						}
					}
				}
			}
		}
		stage('Deploy Docker Image'){
			steps{
				script{
					docker.withRegistry(registryURL, registryCredential){
						dockerImage.push()
						if (env.BRANCH_NAME == 'master') {
						    dockerImage.push("production")
						}
						sh "docker run -d --name sln-staging-" + imageName + " -p :8000 --network=web -l traefik.backend=sln-staging-" + imageName +" -l traefik.frontend.rule=Host:" + imageName + "-staging.calebjones.dev -l traefik.docker.network=web -l traefik.port=8000 " + registry + ":" + imageName + " 'bash' '-c' 'python /code/manage.py runserver 0.0.0.0:8000'"
					}
				}
			}
		}
    }
    post {
        always {
            // This needs to be removed in favor or removing credential files instead.
            sh '''
               rm spacelaunchnow/config.py
               '''
        }
    }
}
