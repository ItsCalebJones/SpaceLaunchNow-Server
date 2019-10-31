pipeline{
	agent any
	
	environment {
		BRANCH = "${BRANCH_NAME}"
		registry="registry.calebjones.dev:5050/sln-server"
		registryURL = "https://registry.calebjones.dev:5050/sln-server"
		registryCredential = 'calebregistry'
		dockerImage = ''
	}
	
	stages{
		stage('Setup'){
			steps {
                if (env.BRANCH_NAME == 'master') {
                    configFile = 'SLNProductionConfig'
                } else {
                    configFile = 'SLNConfig'
                }
				withCredentials([file(credentialsId: configFile, variable: 'configFile')]) {
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
					if(!fileExists("Dockerfile")){
						echo "No Dockerfile";
					}else{
						dockerImage = docker.build registry + ":" + env.BRANCH_NAME + "_" + "b$BUILD_NUMBER"
					}
				}
			}
		}
		stage('Deploy Docker Image'){
			steps{
				script{
					docker.withRegistry(registryURL, registryCredential){
						dockerImage.push()
					}
				}
			}
		}
		stage('Remove Docker Image Locally'){
			steps{
				sh "docker rmi $registry:" + env.BRANCH_NAME + "_" + "b$BUILD_NUMBER"
			}
		}
	}
}
