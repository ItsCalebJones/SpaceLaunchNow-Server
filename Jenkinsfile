pipeline{
	agent any
	
	environment {
		BRANCH = "${BRANCH_NAME}"
	}
	
	stages{
		stage('Setup'){
			steps {
				withCredentials([file(credentialsId: 'SLNConfig', variable: 'configFile')]) {
					sh 'cp $configFile spacelaunchnow/config.py'
				}
				sh 'mkdir -p log'
				sh 'touch log/daily_digest.log'
				withPythonEnv('python3') {
					sh 'python3 -m pip install -r requirements.txt'
				}
			}
		}
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