#!/usr/bin/env groovy

def defineBranchName() {
    def branchName = "${env.BRANCH_NAME}"
    branchName = branchName.replace ('/', '-')
    branchName = branchName.replace ('_', '-')
    branchName = branchName.replace ('.', '')
    return branchName
}

def defineImageName() {
    def branchName = defineBranchName()
    return "${branchName}-b${BUILD_NUMBER}"
}

def commitMessage() {
    def message = sh(returnStdout: true, script: "git log --format='medium' -1 ${GIT_COMMIT}").trim()
    return "${message}"
}

def defineDockerTag() {
    def branchName = "${env.BRANCH_NAME}"
    branchName = branchName.replace ('/', '')
    branchName = branchName.replace ('_', '')
    branchName = branchName.replace ('.', '')
    return "${branchName}b${BUILD_NUMBER}"
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
		doRegistryURL = "https://registry.digitalocean.com/spacelaunchnow-registry"
		doRegistryCredential= 'digitalocean_registry'
		dockerTag = defineDockerTag()
        imageName = defineImageName()
		branchName = defineBranchName()
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
				withPythonEnv('python3') {
					sh 'python3 -m pip install -r requirements.txt'
				}
			}
		}
		stage('Tests'){
			parallel {
				stage('Run Django Tests'){
					steps {
						withPythonEnv('python3') {
							sh 'python3 manage.py test'
						}
					}
				}
				stage('Run Formatting Checks'){
					steps {
						catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
							sh 'pylint **/*.py'
						}
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
					} else {
					    withCredentials([string(credentialsId: 'EXTRA_INDEX_URL', variable: 'INDEX_URL')]) {
                            def buildArg = '--build-arg EXTRA_INDEX_URL="$INDEX_URL" .'
                            def dockerReg = registry + ":" + imageName
                            dockerImage = docker.build(dockerReg, buildArg)
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
						    dockerImage.push("${dockerTag}")
						    dockerImage.push("production")
						}
						sh "docker ps -f name=" + branchName +" -q | xargs --no-run-if-empty docker container stop"
						sh "docker run --rm -d --name sln-staging-" + imageName + " -p :8000 --network=web -l traefik.backend=sln-staging-" + imageName +" -l traefik.frontend.rule=Host:" + imageName + "-staging.calebjones.dev -l traefik.docker.network=web -l traefik.port=8000 " + registry + ":" + imageName + " 'bash' '-c' 'python /code/manage.py runserver 0.0.0.0:8000'"
					}
					docker.withRegistry(doRegistryURL, doRegistryCredential){
						if (env.BRANCH_NAME == 'master') {
						    dockerImage.push("${dockerTag}")
						    dockerImage.push("production")
						}
					}
				}
			}
		}
    }
    post {
        always {

            discordSend description: "**Status:** ${currentBuild.currentResult}\n**Branch: **${env.BRANCH_NAME}\n**Build: **${env.BUILD_NUMBER}\n\n${COMMIT_MESSAGE}\n\nLink: https://" + imageName + "-staging.calebjones.dev",
                footer: "",
                link: env.BUILD_URL,
                result: currentBuild.currentResult,
                title: PROJECT_NAME,
                webhookURL: DISCORD_URL,
                thumbnail: "https://i.imgur.com/FASV6fJ.png",
                notes: "Hey <@&641718676046872588>, new build completed for ${PROJECT_NAME}!"
            // This needs to be removed in favor or removing credential files instead.
            sh '''
               rm spacelaunchnow/config.py
               '''
        }
    }
}
