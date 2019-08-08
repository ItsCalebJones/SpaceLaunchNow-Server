pipeline{
	agent any
	
	environment {
		BRANCH = "${BRANCH_NAME}"
	}
	
	stages{
		stage('Setup'){
			steps {
				echo 'Setting up'
				withCredentials([file(credentialsId: 'SLNConfig', variable: 'configFile')]) {
					sh 'cp $configFile spacelaunchnow/config.py'
				}
				sh """
				mkdir -p log
				touch log/daily_digest.log
				python3 -m venv venv
				. venv/bin/activate
				python3 -m pip install -r requirements.txt
				python3 manage.py test
				"""
			}
		}
		stage('Test'){
			steps {
				echo 'Testing1'
			}
		}
	}
}
