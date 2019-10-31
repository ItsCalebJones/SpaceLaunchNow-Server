pipeline{
	agent any
	
	environment {
		BRANCH = "${BRANCH_NAME}"
		registry="registry.calebjones.dev:5050/sln-server"
		registryURL = "https://registry.calebjones.dev:5050/sln-server"
		registryCredential = 'calebregistry'
		imageName = "${BRANCH_NAME}-b${BUILD_NUMBER}"
		dockerImage = ''
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
					}else{
						dockerImage = docker.build registry + ":" + imageName
					}
				}
			}
		}
		stage('Deploy Docker Image'){
			steps{
				script{
					docker.withRegistry(registryURL, registryCredential){
						dockerImage.push()
						sh "docker run -d --name sln-staging-" + imageName + " -p :8000 --network=web -l traefik.backend=sln-staging-" + imageName +" -l traefik.frontend.rule=Host:" + imageName + ".staging.calebjones.dev -l traefik.docker.network=web -l traefik.port=8000 " + registry + ":" + imageName + " 'bash' '-c' 'python /code/manage.py runserver 0.0.0.0:8000'"
					}
				}
			}
		}
	}
}
