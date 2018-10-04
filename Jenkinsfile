pipeline {
  agent any
  environment
  {    //it was in every stage
    IMAGE_NAME_MAPPA = 'nexus.teamdigitale.test/daf-mappa-quartiere'
  }
  stages {
    stage('Build') {
      steps {
        script {
          slackSend (message: "BUILD START: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' CHECK THE RESULT ON: https://cd.daf.teamdigitale.it/blue/organizations/jenkins/CI-MappaQuartiere/activity")
        sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker build . -t $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID'
        }
      }
    }
    stage('Test') {
      steps { //sh' != sh'' only one sh command
      script {
        sh '''
        COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6);
        CONTAINERID=$(docker run -d -p 3000:3000 $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID);
        sleep 5s;
        curl -s localhost:3000
        curl -s -I localhost:3000 | grep 200;
        docker stop $(docker ps -a -q);
        docker rm $(docker ps -a -q)
  '''
      }
    }
    }
    stage('Upload'){
      steps {
        script {
          if(env.BRANCH_NAME == 'test' || env.BRANCH_NAME == 'production'){
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker push $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID'
            sh 'COMMIT_ID=$(echo ${GIT_COMMIT} | cut -c 1-6); docker rmi $IMAGE_NAME_MAPPA:$BUILD_NUMBER-$COMMIT_ID'
          }
        }
      }
    }
    stage('Staging') {
      steps {
        script {

          if(env.BRANCH_NAME=='test' || env.BRANCH_NAME == 'production'){
          sh ''' COMMIT_ID=$(echo ${GIT_COMMIT}|cut -c 1-6);
              sed "s#image: nexus.teamdigitale.test/daf-mappa.*#image: nexus.teamdigitale.test/daf-mappa-quartiere:$BUILD_NUMBER-$COMMIT_ID#" mappa-quartiere.yaml > mappa-quartiere1.yaml ;kubectl apply -f mappa-quartiere1.yaml --validate=false'''
          slackSend (color: '#00FF00', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' https://cd.daf.teamdigitale.it/blue/organizations/jenkins/CI-MappaQuartiere/activity")
          }
        }
      }
    }
  }
  post {
        failure {
            slackSend (color: '#ff0000', message: "FAIL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' https://cd.daf.teamdigitale.it/blue/organizations/jenkins/CI-MappaQuartiere/activity")
        }
    }
}
